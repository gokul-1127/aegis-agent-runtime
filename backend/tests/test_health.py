"""Tests for the health endpoint."""
from fastapi.testclient import TestClient

from app.main import app


def test_root_endpoint():
    """The root endpoint should return app info."""
    client = TestClient(app)
    response = client.get("/")

    assert response.status_code == 200
    data = response.json()
    assert data["app"] == "AEGIS"
    assert "version" in data


def test_health_endpoint():
    """The health endpoint should return status ok."""
    client = TestClient(app)
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["app"] == "AEGIS"
    assert "version" in data