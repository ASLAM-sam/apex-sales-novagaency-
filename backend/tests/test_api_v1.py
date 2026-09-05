from unittest.mock import AsyncMock, MagicMock
from bson import ObjectId
from fastapi.testclient import TestClient
import pytest
from app.api.routes.businesses import get_business_service
from app.api.routes.campaigns import get_campaign_service
from app.api.routes.conversations import get_conversation_service
from app.api.routes.leads import get_lead_service
from app.api.routes.outreach import get_outreach_service
from app.api.routes.research import get_research_service
from app.api.routes.website_audits import get_audit_service
from app.core.exceptions import ConflictError, InvalidObjectIdError, NotFoundError, ValidationError
from app.main import app
from app.schemas.api import PaginationMetadata
from app.schemas.business import Business
from app.schemas.enums import BusinessStatus
from app.schemas.lead import Lead

client = TestClient(app)


def test_health_check_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "apex-api"


def test_businesses_create_api():
    mock_service = MagicMock()
    fake_id = ObjectId()
    biz = Business(
        id=fake_id,
        name="API Biz",
        normalized_name="api biz",
        business_status=BusinessStatus.ACTIVE,
    )
    mock_service.create_business = AsyncMock(return_value=biz)

    app.dependency_overrides[get_business_service] = lambda: mock_service

    try:
        response = client.post(
            "/api/v1/businesses",
            json={"name": "API Biz"},
        )
        assert response.status_code == 201
        data = response.json()["data"]
        assert data["name"] == "API Biz"
        assert data["id"] == str(fake_id)
    finally:
        app.dependency_overrides.clear()


def test_businesses_list_api():
    mock_service = MagicMock()
    biz = Business(id=ObjectId(), name="API Biz 1")
    meta = PaginationMetadata(page=1, page_size=25, total=1, pages=1)
    mock_service.list_businesses = AsyncMock(return_value=([biz], meta))

    app.dependency_overrides[get_business_service] = lambda: mock_service

    try:
        response = client.get("/api/v1/businesses?page=1&page_size=10")
        assert response.status_code == 200
        res = response.json()
        assert len(res["data"]) == 1
        assert res["pagination"]["total"] == 1
    finally:
        app.dependency_overrides.clear()


def test_businesses_get_by_id_404():
    mock_service = MagicMock()
    fake_id = str(ObjectId())
    mock_service.get_business = AsyncMock(side_effect=NotFoundError(f"Business with ID '{fake_id}' not found."))

    app.dependency_overrides[get_business_service] = lambda: mock_service

    try:
        response = client.get(f"/api/v1/businesses/{fake_id}")
        assert response.status_code == 404
        res = response.json()
        assert res["error"]["code"] == "NOT_FOUND"
    finally:
        app.dependency_overrides.clear()


def test_invalid_object_id_error_handling():
    mock_service = MagicMock()
    mock_service.get_business = AsyncMock(side_effect=InvalidObjectIdError("Invalid ObjectId format: 'bad_id'"))

    app.dependency_overrides[get_business_service] = lambda: mock_service

    try:
        response = client.get("/api/v1/businesses/bad_id")
        assert response.status_code == 422
        res = response.json()
        assert res["error"]["code"] == "INVALID_ID"
    finally:
        app.dependency_overrides.clear()


def test_leads_create_and_get_api():
    mock_service = MagicMock()
    fake_biz_id = str(ObjectId())
    fake_lead_id = str(ObjectId())

    lead = Lead(
        id=fake_lead_id,
        business_id=fake_biz_id,
    )
    mock_service.create_lead = AsyncMock(return_value=lead)
    mock_service.get_lead = AsyncMock(return_value=lead)

    app.dependency_overrides[get_lead_service] = lambda: mock_service

    try:
        # Create lead
        response = client.post("/api/v1/leads", json={"business_id": fake_biz_id})
        assert response.status_code == 201
        data = response.json()["data"]
        assert data["business_id"] == fake_biz_id

        # Get lead
        response_get = client.get(f"/api/v1/leads/{fake_lead_id}")
        assert response_get.status_code == 200
        assert response_get.json()["data"]["id"] == fake_lead_id
    finally:
        app.dependency_overrides.clear()


def test_outreach_unsafe_sent_transition_api():
    mock_service = MagicMock()
    fake_outreach_id = str(ObjectId())
    mock_service.update_outreach = AsyncMock(
        side_effect=ValidationError("Direct transition to status 'SENT' is not permitted via standard update endpoint.")
    )

    app.dependency_overrides[get_outreach_service] = lambda: mock_service

    try:
        response = client.patch(
            f"/api/v1/outreach/{fake_outreach_id}",
            json={"status": "SENT"},
        )
        assert response.status_code == 422
        res = response.json()
        assert res["error"]["code"] == "VALIDATION_ERROR"
        assert "SENT" in res["error"]["message"]
    finally:
        app.dependency_overrides.clear()


def test_openapi_schema_contains_v1_routes():
    response = client.get("/openapi.json")
    assert response.status_code == 200
    openapi = response.json()
    paths = openapi.get("paths", {})

    assert "/api/v1/businesses" in paths
    assert "/api/v1/businesses/{business_id}" in paths
    assert "/api/v1/leads" in paths
    assert "/api/v1/leads/{lead_id}" in paths
    assert "/api/v1/research" in paths
    assert "/api/v1/website-audits" in paths
    assert "/api/v1/outreach" in paths
    assert "/api/v1/conversations" in paths
    assert "/api/v1/campaigns" in paths
    assert "/health" in paths
    assert "/ready" in paths
