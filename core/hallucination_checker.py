import re
import threading
from typing import Optional

import numpy as np
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

import config
from core.embedding_engine import get_embedding_engine
from utils.logger import get_logger

logger = get_logger(__name__)


# Status labels
STATUS_VERIFIED = "VERIFIED"
STATUS_FLAGGED = "FLAGGED"
STATUS_NO_CLAIMS = "NO_CLAIMS"

# NLI label mapping (index -> label) for MoritzLaurer/mDeBERTa-v3-base models
# Standard order: 0=entailment, 1=neutral, 2=contradiction
NLI_LABELS = ["entailment", "neutral", "contradiction"]
NLI_MODEL_NAME = "MoritzLaurer/mDeBERTa-v3-base-xnli-multilingual-nli-2mil7"


class HallucinationChecker:
    """
    Two-stage hallucination verification:

    Stage 1 (cheap): cosine similarity between claim and context chunks.
        - If top-K context similarity < SIMILARITY_GATE -> FLAGGED (no relevant context)
        - Else proceed to stage 2 with top-K context as premise candidates.

    Stage 2 (precise): NLI verification using mDeBERTa-v3 multilingual NLI model.
        - For each claim, run NLI against top-K context chunks.
        - Pick the chunk with highest entailment probability as the verdict.
        - Decision:
            * entailment_prob >= ENTAILMENT_THRESHOLD -> VERIFIED
            * contradiction_prob >= CONTRADICTION_THRESHOLD -> FLAGGED (active contradiction)
            * otherwise -> FLAGGED (insufficient support, neutral)

    overall_score = 1 - avg(per-claim entailment_prob)
        -> 0.0 = fully verified, 1.0 = fully hallucinated
    Complexity: O(c*k) NLI inferences where c=claims, k=top context chunks per claim.
    """

    # Gate before running expensive NLI
    SIMILARITY_GATE = 0.35
    # Top-K context chunks to check per claim (cap NLI calls)
    TOP_K_CONTEXT_FOR_NLI = 2

    _ABBREVIATIONS = {
        "dr", "mr", "mrs", "ms", "no", "vs", "etc", "dll", "dsb", "tsb",
        "yth", "drs", "drg", "prof", "ir", "st", "mt", "se",
        "jan", "feb", "mar", "apr", "jun", "jul", "agu", "sep", "okt", "nov", "des",
    }

    _REFUSAL_MARKERS = [
        "tidak ada informasi",
        "tidak ditemukan",
        "tidak mengandung",
        "tidak memuat",
        "do not contain",
        "does not contain",
        "no information",
        "cannot find",
        "insufficient information",
        "tidak cukup informasi",
        "tidak dapat menjawab",
    ]

    _instance: Optional["HallucinationChecker"] = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True

        self.embedder = get_embedding_engine()
        self.threshold = config.HALLUCINATION_THRESHOLD  # legacy, kept for reference
        self.ENTAILMENT_THRESHOLD = config.NLI_ENTAILMENT_THRESHOLD
        self.CONTRADICTION_THRESHOLD = config.NLI_CONTRADICTION_THRESHOLD

        logger.info(f"Loading NLI model: {NLI_MODEL_NAME}")
        self.nli_tokenizer = AutoTokenizer.from_pretrained(NLI_MODEL_NAME)
        self.nli_model = AutoModelForSequenceClassification.from_pretrained(NLI_MODEL_NAME)
        self.nli_model.eval()
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.nli_model.to(self.device)
        logger.info(f"NLI model loaded on {self.device}")

    # ---------- Refusal detection ----------

    def _is_refusal(self, text: str) -> bool:
        low = text.lower().strip()
        return any(marker in low for marker in self._REFUSAL_MARKERS)

    # ---------- Claim extraction ----------

    def _extract_claims(self, answer: str) -> list[str]:
        if not answer or not answer.strip():
            return []

        cleaned = re.sub(r"\[Document\s*\d+\]", "", answer, flags=re.IGNORECASE)
        cleaned = re.sub(r"\[Dokumen\s*\d+\]", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s+", " ", cleaned).strip()

        sentences = []
        current = []
        i = 0
        text = cleaned
        while i < len(text):
            ch = text[i]
            current.append(ch)
            if ch in ".!?;":
                buf = "".join(current).strip()
                last_word = re.split(r"[\s,;:]", buf)[-1].rstrip(".!?;").lower()
                if last_word in self._ABBREVIATIONS:
                    i += 1
                    continue
                if i + 1 < len(text) and text[i + 1].isdigit():
                    i += 1
                    continue
                sentences.append(buf)
                current = []
            i += 1
        tail = "".join(current).strip()
        if tail:
            sentences.append(tail)

        claims = []
        for s in sentences:
            s = s.strip(".!?;: \t\n")
            if len(s.split()) >= 3 and re.search(r"[A-Za-zÀ-ÿ]", s):
                claims.append(s)
        return claims

    # ---------- NLI inference ----------

    @torch.no_grad()
    def _nli_score(self, premise: str, hypothesis: str) -> dict:
        """
        Run NLI on (premise, hypothesis). Returns dict of label -> probability.
        Truncates premise/hypothesis to fit model max length.
        """
        inputs = self.nli_tokenizer(
            premise,
            hypothesis,
            return_tensors="pt",
            truncation=True,
            max_length=512,
        ).to(self.device)
        outputs = self.nli_model(**inputs)
        probs = torch.softmax(outputs.logits, dim=-1)[0].cpu().numpy()
        return {NLI_LABELS[i]: float(probs[i]) for i in range(len(NLI_LABELS))}

    # ---------- Public API ----------

    def check(self, answer: str, context_chunks: list[dict]) -> dict:
        """
        Verify claims via cosine-gate + NLI.

        Returns:
            {
                "status": VERIFIED | FLAGGED | NO_CLAIMS,
                "overall_score": float (0=verified, 1=hallucinated),
                "claims": [
                    {
                        "claim": str,
                        "status": VERIFIED | FLAGGED,
                        "max_similarity": float,
                        "entailment": float,
                        "neutral": float,
                        "contradiction": float,
                        "verdict": "entailment" | "neutral" | "contradiction" | "no_context",
                        "best_source": str | None,
                    }, ...
                ],
                "summary": str,
            }
        """
        if not answer or not answer.strip():
            return {
                "status": STATUS_NO_CLAIMS,
                "overall_score": 0.0,
                "claims": [],
                "summary": "Empty answer",
            }

        if self._is_refusal(answer):
            logger.info("Hallucination check: refusal detected, no claims")
            return {
                "status": STATUS_NO_CLAIMS,
                "overall_score": 0.0,
                "claims": [],
                "summary": "Answer indicates no information available (safe refusal)",
            }

        claims = self._extract_claims(answer)
        if not claims:
            return {
                "status": STATUS_NO_CLAIMS,
                "overall_score": 0.0,
                "claims": [],
                "summary": "No verifiable claims extracted",
            }

        if not context_chunks:
            return {
                "status": STATUS_FLAGGED,
                "overall_score": 1.0,
                "claims": [{
                    "claim": c,
                    "status": STATUS_FLAGGED,
                    "max_similarity": 0.0,
                    "entailment": 0.0,
                    "neutral": 0.0,
                    "contradiction": 0.0,
                    "verdict": "no_context",
                    "best_source": None,
                } for c in claims],
                "summary": "No context to verify against — all claims flagged",
            }

        # Pre-compute embeddings for cosine gate
        ctx_texts = [c.get("text", "") for c in context_chunks]
        ctx_sources = [c.get("filename", "unknown") for c in context_chunks]
        ctx_matrix = self.embedder.encode_batch(ctx_texts)
        claim_matrix = self.embedder.encode_batch(claims)
        sims = claim_matrix @ ctx_matrix.T  # (n_claims, n_ctx)

        claim_results = []
        entailment_scores = []

        for i, claim in enumerate(claims):
            # Pick top-K context chunks by cosine similarity
            sorted_idx = np.argsort(-sims[i])[: self.TOP_K_CONTEXT_FOR_NLI]
            best_sim = float(sims[i][sorted_idx[0]])

            # Gate: if best similarity is too low, no relevant context exists
            if best_sim < self.SIMILARITY_GATE:
                claim_results.append({
                    "claim": claim,
                    "status": STATUS_FLAGGED,
                    "max_similarity": round(best_sim, 4),
                    "entailment": 0.0,
                    "neutral": 0.0,
                    "contradiction": 0.0,
                    "verdict": "no_context",
                    "best_source": ctx_sources[sorted_idx[0]],
                })
                entailment_scores.append(0.0)
                continue

            # Run NLI against top-K context chunks; pick best entailment
            best_nli = None
            best_idx = sorted_idx[0]
            for idx in sorted_idx:
                nli = self._nli_score(premise=ctx_texts[idx], hypothesis=claim)
                if best_nli is None or nli["entailment"] > best_nli["entailment"]:
                    best_nli = nli
                    best_idx = idx
                # Early stop: strong entailment -> no need to check others
                if best_nli["entailment"] >= self.ENTAILMENT_THRESHOLD + 0.2:
                    break

            ent = best_nli["entailment"]
            neu = best_nli["neutral"]
            con = best_nli["contradiction"]

            # Decision
            if con >= self.CONTRADICTION_THRESHOLD:
                verdict = "contradiction"
                status = STATUS_FLAGGED
            elif ent >= self.ENTAILMENT_THRESHOLD:
                verdict = "entailment"
                status = STATUS_VERIFIED
            else:
                verdict = "neutral"
                status = STATUS_FLAGGED

            claim_results.append({
                "claim": claim,
                "status": status,
                "max_similarity": round(best_sim, 4),
                "entailment": round(ent, 4),
                "neutral": round(neu, 4),
                "contradiction": round(con, 4),
                "verdict": verdict,
                "best_source": ctx_sources[int(best_idx)],
            })
            entailment_scores.append(ent)

        avg_entailment = sum(entailment_scores) / len(entailment_scores) if entailment_scores else 0.0
        overall_score = round(1.0 - avg_entailment, 4)
        flagged_count = sum(1 for r in claim_results if r["status"] == STATUS_FLAGGED)

        if flagged_count > 0:
            overall_status = STATUS_FLAGGED
            summary = (
                f"{flagged_count}/{len(claims)} claim(s) flagged via NLI "
                f"(hallucination_score={overall_score})"
            )
        else:
            overall_status = STATUS_VERIFIED
            summary = (
                f"All {len(claims)} claim(s) verified via NLI "
                f"(hallucination_score={overall_score})"
            )

        logger.info(f"Hallucination check: {summary}")
        return {
            "status": overall_status,
            "overall_score": overall_score,
            "claims": claim_results,
            "summary": summary,
        }


def get_hallucination_checker() -> HallucinationChecker:
    return HallucinationChecker()