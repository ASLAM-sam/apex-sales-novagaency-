import pytest
from app.core.config import Settings
from app.db.mongodb import MongoDBManager, check_mongodb_health


def test_mongodb_configuration_defaults():
    settings = Settings()
    assert settings.MONGODB_DATABASE == "apex_sales"
    assert settings.MONGODB_SERVER_SELECTION_TIMEOUT_MS == 5000
    assert settings.mongodb_database == "apex_sales"


def test_sanitize_connection_string():
    manager = MongoDBManager()
    sensitive_uri = "mongodb+srv://admin_user:secret_pass123@cluster0.mongodb.net/apex_sales"
    sanitized = manager.sanitize_connection_string(sensitive_uri)
    assert "secret_pass123" not in sanitized
    assert "admin_user" not in sanitized
    assert "mongodb+srv://***:***@cluster0.mongodb.net/apex_sales" in sanitized


@pytest.mark.anyio
async def test_unconfigured_mongodb_health():
    manager = MongoDBManager()
    health = await manager.check_health()
    assert health["status"] == "unhealthy"
    assert "not configured" in health["details"].lower() or "not initialized" in health["details"].lower()
