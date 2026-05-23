from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from models.database import Base


class Document(Base):
    __tablename__ = "documents"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    user_id     = Column(Integer, ForeignKey("users.id"), nullable=False)
    filename    = Column(String, nullable=False)
    filepath    = Column(String, nullable=False)
    text        = Column(Text, nullable=False)
    word_count  = Column(Integer, default=0)
    dates       = Column(String, nullable=True)
    is_shared   = Column(Boolean, default=False)
    created_at  = Column(DateTime, default=datetime.utcnow)
    chunk_index = Column(Integer, default=0)   # 0-based chunk index
    chunk_total = Column(Integer, default=1)   # total chunks for this file

    owner     = relationship("User", back_populates="documents")
    embedding = relationship("Embedding", back_populates="document", uselist=False, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id":          self.id,
            "user_id":     self.user_id,
            "filename":    self.filename,
            "word_count":  self.word_count,
            "dates":       self.dates,
            "is_shared":   self.is_shared,
            "created_at":  self.created_at.isoformat() if self.created_at else None,
            "chunk_index": self.chunk_index,
            "chunk_total": self.chunk_total,
        }
