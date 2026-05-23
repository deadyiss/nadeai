import pytest
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set test environment
os.environ["FLASK_ENV"] = "testing"
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["GROQ_API_KEY"] = "test_key_xyz"


@pytest.fixture
def app():
    """Create app for testing."""
    from app import create_app
    app = create_app()
    app.config["TESTING"] = True
    return app


@pytest.fixture
def client(app):
    """Test client."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """CLI runner."""
    return app.test_cli_runner()
