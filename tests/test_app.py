"""Test Flask application."""
import pytest


def test_app_exists(app):
    """Test app is created."""
    assert app is not None


def test_app_testing_mode(app):
    """Test app is in testing mode."""
    assert app.config["TESTING"] is True


def test_health_endpoint(client):
    """Test health check endpoint."""
    response = client.get("/health")
    # Allow 200 (healthy) or 503 (service unavailable - e.g. invalid API key in test)
    assert response.status_code in [200, 503]
    data = response.get_json()
    assert "data" in data
    assert "status" in data["data"]


def test_login_page(client):
    """Test login page loads."""
    response = client.get("/")
    assert response.status_code == 200 or response.status_code == 302  # May redirect


def test_404_error(client):
    """Test 404 handling."""
    response = client.get("/nonexistent-page")
    assert response.status_code == 404
