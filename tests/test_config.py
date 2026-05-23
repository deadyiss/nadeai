"""Test configuration module."""
import pytest
import os


def test_config_defaults():
    """Test default configuration values."""
    import config

    assert config.FLASK_ENV in ["development", "testing", "production"]
    assert config.FLASK_PORT == 5000 or isinstance(config.FLASK_PORT, int)
    assert config.SECRET_KEY is not None and len(config.SECRET_KEY) >= 10
    assert config.MAX_FILE_SIZE_MB > 0
    assert config.HALLUCINATION_THRESHOLD >= 0
    assert config.TOP_K_DOCUMENTS > 0
    assert config.SIMILARITY_MIN_THRESHOLD >= 0


def test_groq_config():
    """Test Groq API configuration."""
    import config

    # In test environment, GROQ_API_KEY should be set (from conftest)
    assert config.GROQ_API_KEY is not None
    assert config.LLM_PROVIDER == "groq"
    assert config.LLM_MODEL is not None


def test_database_config():
    """Test database configuration."""
    import config

    assert config.DATABASE_URL is not None
    assert "sqlite" in config.DATABASE_URL or "postgresql" in config.DATABASE_URL


def test_nli_thresholds():
    """Test NLI threshold values are valid."""
    import config

    assert 0 <= config.NLI_ENTAILMENT_THRESHOLD <= 1
    assert 0 <= config.NLI_CONTRADICTION_THRESHOLD <= 1
