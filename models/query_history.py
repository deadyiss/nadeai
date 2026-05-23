from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, Float, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from models.database import Base


class QueryHistory(Base):
    __tablename__ = "query_history"

    id             = Column(Integer, primary_key=True, autoincrement=True)
    user_id        = Column(Integer, ForeignKey("users.id"), nullable=False)
    query_text     = Column(Text, nullable=False)
    answer         = Column(Text, nullable=True)
    sources        = Column(Text, nullable=True)
    confidence     = Column(Float, nullable=True)
    has_conflict   = Column(Boolean, default=False)
    execution_time = Column(Float, nullable=True)
    created_at     = Column(DateTime, default=datetime.utcnow)

    user      = relationship("User", back_populates="queries")
    conflicts = relationship("ConflictLog", back_populates="query", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id":             self.id,
            "user_id":        self.user_id,
            "query_text":     self.query_text,
            "answer":         self.answer,
            "sources":        self.sources,
            "confidence":     self.confidence,
            "has_conflict":   self.has_conflict,
            "execution_time": self.execution_time,
            "created_at":     self.created_at.isoformat() if self.created_at else None,
        }
