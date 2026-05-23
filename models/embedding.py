from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship

from models.database import Base


class Embedding(Base):
    __tablename__ = "embeddings_cache"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    doc_id     = Column(Integer, ForeignKey("documents.id"), nullable=False, unique=True)
    embedding  = Column(Text, nullable=False)
    model_name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    document = relationship("Document", back_populates="embedding")


# Alias untuk kompatibilitas (vector_store.py & engine baru pakai nama ini)
EmbeddingCache = Embedding