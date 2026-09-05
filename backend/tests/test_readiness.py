from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_readiness_endpoint_unhealthy():
    with patch("app.api.router.get_database_health", new_callable=AsyncMock) as mock_health:
        mock_health.return_value = {
            "mongodb": {"status": "unhealthy", "details": "MongoDB URI not configured"},
            "sqlite": {"status": "healthy"},
        }
        response = client.get("/ready")
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "not_ready"
        assert data["mongodb"] == "unhealthy"
        assert data["sqlite"] == "healthy"


def test_readiness_endpoint_healthy():
    with patch("app.api.router.get_database_health", new_callable=AsyncMock) as mock_health:
        mock_health.return_value = {
            "mongodb": {"status": "healthy"},
            "sqlite": {"status": "healthy"},
        }
        response = client.get("/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert data["mongodb"] == "healthy"
        assert data["sqlite"] == "healthy"
