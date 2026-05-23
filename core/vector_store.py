import json
import threading
from typing import Optional

import numpy as np
from sqlalchemy.orm import Session

import config
from core.embedding_engine import get_embedding_engine
from models import get_session, Document, EmbeddingCache
from utils.logger import get_logger

logger = get_logger(__name__)


class VectorStore:
    """
    In-memory NumPy dict for embeddings, persisted to SQLite (embeddings_cache).
    On startup, loads all cached embeddings from DB.
    """

    _instance: Optional["VectorStore"] = None
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
        self.dim = self.embedder.dim

        # In-memory store: doc_id -> np.ndarray
        self._vectors: dict[int, np.ndarray] = {}
        # Cache metadata for fast lookup: doc_id -> {"filename", "user_id", "is_shared", "text"}
        self._meta: dict[int, dict] = {}

        self._store_lock = threading.RLock()
        self._load_from_db()

    def _load_from_db(self) -> None:
        logger.info("Loading embeddings from SQLite into memory")
        loaded = 0
        with get_session() as session:
            rows = (
                session.query(EmbeddingCache, Document)
                .join(Document, EmbeddingCache.doc_id == Document.id)
                .all()
            )
            for emb_row, doc_row in rows:
                try:
                    arr = np.array(json.loads(emb_row.embedding), dtype=np.float32)
                    if arr.shape[0] != self.dim:
                        logger.warning(
                            f"Skip doc_id={doc_row.id}: dim mismatch "
                            f"({arr.shape[0]} != {self.dim})"
                        )
                        continue
                    self._vectors[doc_row.id] = arr
                    self._meta[doc_row.id] = {
                        "filename": doc_row.filename,
                        "user_id": doc_row.user_id,
                        "is_shared": doc_row.is_shared,
                        "text": doc_row.text,
                    }
                    loaded += 1
                except Exception as e:
                    logger.warning(f"Failed to load embedding for doc_id={doc_row.id}: {e}")
        logger.info(f"Loaded {loaded} embeddings into memory")

    def add(self, document: Document, session: Session) -> None:
        """
        Generate embedding for document and persist to DB + memory.
        Caller is responsible for committing the session.
        """
        with self._store_lock:
            if document.id is None:
                raise ValueError("Document must be committed (have id) before add")

            vec = self.embedder.encode(document.text)

            existing = (
                session.query(EmbeddingCache)
                .filter(EmbeddingCache.doc_id == document.id)
                .one_or_none()
            )
            payload = json.dumps(vec.tolist())
            if existing is None:
                cache = EmbeddingCache(
                    doc_id=document.id,
                    embedding=payload,
                    model_name=self.embedder.model_name,
                )
                session.add(cache)
            else:
                existing.embedding = payload
                existing.model_name = self.embedder.model_name

            self._vectors[document.id] = vec
            self._meta[document.id] = {
                "filename": document.filename,
                "user_id": document.user_id,
                "is_shared": document.is_shared,
                "text": document.text,
            }
            logger.info(f"Vector added: doc_id={document.id} filename={document.filename}")

    def remove(self, doc_id: int, session: Session) -> None:
        with self._store_lock:
            self._vectors.pop(doc_id, None)
            self._meta.pop(doc_id, None)
            session.query(EmbeddingCache).filter(EmbeddingCache.doc_id == doc_id).delete()
            logger.info(f"Vector removed: doc_id={doc_id}")

    def search(
        self,
        query: str,
        top_k: int = None,
        user_id: Optional[int] = None,
        include_shared: bool = True,
        min_similarity: float = None,
    ) -> list[dict]:
        """
        Returns: list of {"doc_id", "filename", "text", "similarity", "user_id", "is_shared"}
        sorted by similarity desc.
        Scope: documents owned by user_id, plus shared docs if include_shared=True.
        If user_id is None -> search all (admin scope).
        """
        top_k = top_k if top_k is not None else config.TOP_K_DOCUMENTS
        min_similarity = min_similarity if min_similarity is not None else config.SIMILARITY_MIN_THRESHOLD

        if not self._vectors:
            return []

        with self._store_lock:
            # Filter doc_ids by scope
            candidate_ids = []
            for doc_id, meta in self._meta.items():
                if user_id is None:
                    candidate_ids.append(doc_id)
                else:
                    if meta["user_id"] == user_id:
                        candidate_ids.append(doc_id)
                    elif include_shared and meta["is_shared"]:
                        candidate_ids.append(doc_id)

            if not candidate_ids:
                return []

            q_vec = self.embedder.encode(query)

            # Stack candidate vectors
            matrix = np.stack([self._vectors[i] for i in candidate_ids])
            # Cosine sim = dot product (vectors already normalized)
            sims = matrix @ q_vec

            # Pair, filter by threshold, sort
            scored = [
                (candidate_ids[i], float(sims[i]))
                for i in range(len(candidate_ids))
                if sims[i] >= min_similarity
            ]
            scored.sort(key=lambda x: x[1], reverse=True)
            scored = scored[:top_k]

            results = []
            for doc_id, sim in scored:
                meta = self._meta[doc_id]
                results.append({
                    "doc_id": doc_id,
                    "filename": meta["filename"],
                    "text": meta["text"],
                    "similarity": sim,
                    "user_id": meta["user_id"],
                    "is_shared": meta["is_shared"],
                })
            return results

    def stats(self) -> dict:
        with self._store_lock:
            return {
                "total_vectors": len(self._vectors),
                "dimension": self.dim,
                "model": self.embedder.model_name,
            }


def get_vector_store() -> VectorStore:
    return VectorStore()