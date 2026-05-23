from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from models.database import Base


class ConflictLog(Base):
    __tablename__ = "conflicts_log"

    id            = Column(Integer, primary_key=True, autoincrement=True)
    query_id      = Column(Integer, ForeignKey("query_history.id"), nullable=False)
    conflict_type = Column(String, nullable=False)
    description   = Column(Text, nullable=True)
    affected_docs = Column(Text, nullable=True)
    severity      = Column(String, nullable=True)
    created_at    = Column(DateTime, default=datetime.utcnow)

    query = relationship("QueryHistory", back_populates="conflicts")

    def to_dict(self):
        return {
            "id":            self.id,
            "query_id":      self.query_id,
            "conflict_type": self.conflict_type,
            "description":   self.description,
            "affected_docs": self.affected_docs,
            "severity":      self.severity,
            "created_at":    self.created_at.isoformat() if self.created_at else None,
        }
