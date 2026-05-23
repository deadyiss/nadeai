import threading
from typing import Optional

import numpy as np
from sentence_transformers import SentenceTransformer

import config
from utils.logger import get_logger

logger = get_logger(__name__)


class EmbeddingEngine:
    _instance: Optional["EmbeddingEngine"] = None
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

        self.model_name = config.EMBEDDING_MODEL
        self.dim = config.EMBEDDING_DIM

        logger.info(f"Loading embedding model: {self.model_name}")
        self.model = SentenceTransformer(self.model_name)
        actual_dim = self.model.get_sentence_embedding_dimension()
        if actual_dim != self.dim:
            logger.warning(
                f"Configured EMBEDDING_DIM={self.dim} but model has {actual_dim}. "
                f"Using actual: {actual_dim}"
            )
            self.dim = actual_dim
        logger.info(f"Embedding model loaded. Dimension: {self.dim}")

    def encode(self, text: str) -> np.ndarray:
        if not text or not text.strip():
            raise ValueError("Cannot encode empty text")
        vec = self.model.encode(
            text, convert_to_numpy=True, normalize_embeddings=True
        )
        return vec.astype(np.float32)

    def encode_batch(self, texts: list[str], batch_size: int = 32) -> np.ndarray:
        if not texts:
            return np.zeros((0, self.dim), dtype=np.float32)
        cleaned = [t if t and t.strip() else " " for t in texts]
        vecs = self.model.encode(
            cleaned,
            convert_to_numpy=True,
            normalize_embeddings=True,
            batch_size=batch_size,
            show_progress_bar=False,
        )
        return vecs.astype(np.float32)

    @staticmethod
    def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
        """Vectors are normalized -> dot product equals cosine similarity."""
        return float(np.dot(a, b))


def get_embedding_engine() -> EmbeddingEngine:
    return EmbeddingEngine()