import os
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

import config

Base = declarative_base()
engine = create_engine(
    config.DATABASE_URL,
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Generator-style session (FastAPI-compatible). Use in routes."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_session():
    """Context manager session. Use in scripts and core modules."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.makedirs(os.path.join(base_dir, "data"), exist_ok=True)
    os.makedirs(config.UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(config.TEMP_UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(config.LOG_FOLDER, exist_ok=True)

    from models.user import User
    from models.document import Document
    from models.embedding import Embedding, EmbeddingCache  # noqa: F401
    from models.query_history import QueryHistory
    from models.session import Session
    from models.conflict_log import ConflictLog

    Base.metadata.create_all(bind=engine)
    print("Database initialized successfully.")