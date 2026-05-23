"""Test basic imports and module structure."""
import pytest


def test_config_import():
    """Test config module loads."""
    import config
    assert hasattr(config, "FLASK_ENV")
    assert hasattr(config, "LLM_PROVIDER")
    assert hasattr(config, "DATABASE_URL")


def test_core_modules_import():
    """Test core modules load."""
    from core import llm_engine
    from core import hallucination_checker
    from core import query_processor
    from core import conflict_detector

    assert llm_engine is not None
    assert hallucination_checker is not None
    assert query_processor is not None
    assert conflict_detector is not None


def test_models_import():
    """Test database models load."""
    from models.database import init_db
    from models.user import User
    from models.document import Document
    from models.query_history import QueryHistory
    from models.embedding import Embedding

    assert Document is not None
    assert User is not None
    assert QueryHistory is not None
    assert Embedding is not None


def test_utils_import():
    """Test utility modules load."""
    from utils import file_validator
    from utils import logger
    from utils import response_builder

    assert file_validator is not None
    assert logger is not None
    assert response_builder is not None
