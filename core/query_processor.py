import json
import time
from typing import Optional

from core.conflict_detector import get_conflict_detector
from core.hallucination_checker import get_hallucination_checker, STATUS_NO_CLAIMS, STATUS_VERIFIED
from core.llm_engine import get_llm_engine
from core.vector_store import get_vector_store
from models import get_session, QueryHistory
from utils.logger import get_logger

logger = get_logger(__name__)


class QueryProcessor:
    """
    Orchestrates the full RAG pipeline:
    1. Retrieve top-K relevant docs (vector_store)
    2. Detect conflicts across retrieved docs (conflict_detector)
    3. Generate answer (llm_engine)
    4. Verify claims (hallucination_checker)
    5. Compute confidence
    6. Persist query to history
    7. Return structured response
    """

    def __init__(self):
        self.store = get_vector_store()
        self.llm = get_llm_engine()
        self.conflict_detector = get_conflict_detector()
        self.hallucination_checker = get_hallucination_checker()

    def _compute_confidence(
        self,
        search_hits: list[dict],
        hallucination_score: float,
        has_conflict: bool,
        is_refusal: bool,
    ) -> float:
        """
        Confidence score 0-1.
        Formula:
            base = avg(top similarities)
            penalty_hallucination = hallucination_score (0-1)
            penalty_conflict = 0.2 if has_conflict else 0
            confidence = base * (1 - penalty_hallucination) - penalty_conflict
            clamp to [0, 1]
        If refusal (LLM said "no info"), confidence is treated as the avg similarity
        directly (no hallucination penalty since there are no claims).
        """
        if not search_hits:
            return 0.0

        sims = [h.get("similarity", 0) for h in search_hits]
        base = sum(sims) / len(sims)

        if is_refusal:
            # Refusal is a safe answer; confidence is just retrieval strength
            score = base
        else:
            score = base * (1.0 - hallucination_score)

        if has_conflict:
            score -= 0.2

        return max(0.0, min(1.0, score))

    def _persist_history(
        self,
        user_id: Optional[int],
        query_text: str,
        answer: str,
        sources: list[dict],
        confidence: float,
        has_conflict: bool,
        execution_time_ms: float,
        conflicts: list[dict],
    ) -> Optional[int]:
        """Save query + conflicts to DB. Returns query_history id, or None on failure."""
        if user_id is None:
            return None

        try:
            with get_session() as s:
                qh = QueryHistory(
                    user_id=user_id,
                    query_text=query_text,
                    answer=answer,
                    sources=json.dumps(sources),
                    confidence=float(confidence),
                    has_conflict=bool(has_conflict),
                    execution_time=float(execution_time_ms),
                )
                s.add(qh)
                s.commit()
                s.refresh(qh)
                query_id = qh.id

                # Persist conflicts
                if conflicts:
                    from models import ConflictLog
                    for c in conflicts:
                        cl = ConflictLog(
                            query_id=query_id,
                            conflict_type=c["conflict_type"],
                            description=c["description"],
                            affected_docs=json.dumps(c["affected_docs"]),
                            severity=c["severity"],
                        )
                        s.add(cl)
                    s.commit()

                return query_id
        except Exception as e:
            logger.error(f"Failed to persist query history: {e}")
            return None

    def process(
        self,
        query: str,
        user_id: Optional[int] = None,
        include_shared: bool = True,
        top_k: Optional[int] = None,
        save_history: bool = True,
    ) -> dict:
        """
        Process a query end-to-end.

        Returns:
        {
            "query": str,
            "answer": str,
            "sources": [{"doc_id", "filename", "similarity"}],
            "confidence": float (0-1),
            "has_conflict": bool,
            "conflict_details": [...],
            "hallucination": {"status", "overall_score", "claims": [...], "summary"},
            "execution_time_ms": float,
            "stages": {"search_ms", "conflict_ms", "llm_ms", "hallucination_ms"},
            "query_id": int | None,
        }
        """
        t_total = time.time()
        stages = {}

        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        # 1. Retrieve
        t0 = time.time()
        hits = self.store.search(
            query=query,
            top_k=top_k,
            user_id=user_id,
            include_shared=include_shared,
        )
        stages["search_ms"] = round((time.time() - t0) * 1000, 2)
        logger.info(f"Search: {len(hits)} hits in {stages['search_ms']}ms")

        # 2. Conflict detection
        t0 = time.time()
        conflict_result = self.conflict_detector.detect(hits)
        stages["conflict_ms"] = round((time.time() - t0) * 1000, 2)

        # 3. LLM
        t0 = time.time()
        if hits:
            context_chunks = [
                {"filename": h["filename"], "text": h["text"], "similarity": h["similarity"]}
                for h in hits
            ]
            llm_result = self.llm.answer(query, context_chunks)
            answer_text = llm_result["text"]
        else:
            answer_text = "The documents do not contain enough information to answer this."
            context_chunks = []
        stages["llm_ms"] = round((time.time() - t0) * 1000, 2)

        # 4. Hallucination check
        t0 = time.time()
        hallucination_result = self.hallucination_checker.check(answer_text, context_chunks)
        stages["hallucination_ms"] = round((time.time() - t0) * 1000, 2)

        # 5. Confidence
        is_refusal = hallucination_result["status"] == STATUS_NO_CLAIMS
        confidence = self._compute_confidence(
            search_hits=hits,
            hallucination_score=hallucination_result["overall_score"],
            has_conflict=conflict_result["has_conflict"],
            is_refusal=is_refusal,
        )

        # 6. Build sources payload
        sources = [
            {
                "doc_id": h["doc_id"],
                "filename": h["filename"],
                "similarity": round(h["similarity"], 4),
            }
            for h in hits
        ]

        total_ms = round((time.time() - t_total) * 1000, 2)

        # 7. Persist history
        query_id = None
        if save_history and user_id is not None:
            query_id = self._persist_history(
                user_id=user_id,
                query_text=query,
                answer=answer_text,
                sources=sources,
                confidence=confidence,
                has_conflict=conflict_result["has_conflict"],
                execution_time_ms=total_ms,
                conflicts=conflict_result["conflicts"],
            )

        return {
            "query": query,
            "answer": answer_text,
            "sources": sources,
            "confidence": round(confidence, 4),
            "has_conflict": conflict_result["has_conflict"],
            "conflict_details": conflict_result["conflicts"],
            "hallucination": hallucination_result,
            "execution_time_ms": total_ms,
            "stages": stages,
            "query_id": query_id,
        }


_processor: Optional[QueryProcessor] = None


def get_query_processor() -> QueryProcessor:
    global _processor
    if _processor is None:
        _processor = QueryProcessor()
    return _processor