from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from models.database import Base


class User(Base):
    __tablename__ = "users"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    username   = Column(String, unique=True, nullable=False)
    password   = Column(String, nullable=False)
    email      = Column(String, unique=True, nullable=True)
    role       = Column(String, default="user")
    is_active  = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    documents = relationship("Document", back_populates="owner", cascade="all, delete-orphan")
    queries   = relationship("QueryHistory", back_populates="user", cascade="all, delete-orphan")
    sessions  = relationship("Session", back_populates="user", cascade="all, delete-orphan")

    def to_dict(self):
        return {
            "id":         self.id,
            "username":   self.username,
            "email":      self.email,
            "role":       self.role,
            "is_active":  self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
