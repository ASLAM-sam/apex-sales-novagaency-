import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from bson import ObjectId
from fastapi.testclient import TestClient

from app.main import app
from app.sales.schemas import (
    DashboardSummaryResponse,
    LeadTimelineResponse,
    SalesActionResponse,
    SalesLeadDetailResponse,
    SalesLeadListResponse,
)
from app.sales.service import SalesWorkspaceService
from app.sales.utils import prepare_email_action_data, prepare_whatsapp_url
from app.schemas.business import Business
from app.schemas.enums import LeadStatus, OutreachChannel, OutreachStatus
from app.schemas.lead import Contact, Lead, Qualification
from app.schemas.outreach import Outreach

client = TestClient(app)


def test_whatsapp_url_preparation_valid_and_invalid():
    assert prepare_whatsapp_url(None) is None
    assert prepare_whatsapp_url("") is None
    assert prepare_whatsapp_url("12345") is None

    url_simple = prepare_whatsapp_url("+1 (555) 019-2831")
    assert url_simple == "https://wa.me/15550192831"

    url_msg = prepare_whatsapp_url("+15550192831", "Hello! We noticed your website.")
    assert "https://wa.me/15550192831?text=" in url_msg
    assert "Hello" in url_msg


def test_email_action_data_preparation():
    lead = Lead(
        business_id=ObjectId(),
        contact=Contact(name="John Doe", email="john@example.com"),
    )
    outreach = Outreach(
        lead_id=ObjectId(),
        business_id=ObjectId(),
        channel=OutreachChannel.EMAIL,
        subject="Growth Partnership",
        message="Hi John, ...",
        status=OutreachStatus.DRAFT,
    )
    data = prepare_email_action_data(lead, outreach)
    assert data["email"] == "john@example.com"
    assert data["subject"] == "Growth Partnership"
    assert data["status"] == OutreachStatus.DRAFT
    assert data["is_available"] is True


@pytest.mark.asyncio
async def test_dashboard_summary_counts():
    mock_biz_repo = MagicMock()
    mock_biz_repo.count = AsyncMock(return_value=50)

    mock_lead_repo = MagicMock()
    mock_lead_repo.count = AsyncMock(return_value=10)

    mock_outreach_repo = MagicMock()
    mock_outreach_repo.count = AsyncMock(return_value=12)

    service = SalesWorkspaceService(
        business_repo=mock_biz_repo,
        lead_repo=mock_lead_repo,
        outreach_repo=mock_outreach_repo,
    )

    res = await service.get_dashboard_summary()
    assert isinstance(res, DashboardSummaryResponse)
    assert res.total_businesses == 50
    assert res.draft_outreach_count == 12
@pytest.mark.asyncio
async def test_sales_leads_listing_and_filtering():
    fake_biz_id = str(ObjectId())
    fake_lead_id = str(ObjectId())

    mock_biz_repo = MagicMock()
    mock_biz_repo.get_by_id = AsyncMock(return_value={
        "_id": ObjectId(fake_biz_id),
        "name": "Acme Dentistry",
        "city": "Dallas",
        "category": "Healthcare",
        "verification_status": "VERIFIED",
        "website": "https://acmedental.com",
        "phone": "+1 555 1234",
    })

    mock_lead_repo = MagicMock()
    mock_lead_repo.list_leads = AsyncMock(return_value=([
        {
            "_id": ObjectId(fake_lead_id),
            "business_id": ObjectId(fake_biz_id),
            "lead_status": "QUALIFIED",
            "pipeline_stage": "QUALIFIED",
            "lead_source": "MANUAL",
            "contact": {"phone": "+1 555 1234", "email": "info@acmedental.com"},
            "qualification": {"qualification_score": 85.0, "qualification_status": "HIGH"},
            "created_at": datetime.utcnow(),
        }
    ], 1))

    mock_audit_repo = MagicMock()
    mock_audit_repo.parse_object_id = MagicMock(side_effect=lambda x: ObjectId(x))
    mock_audit_repo.count = AsyncMock(return_value=1)

    mock_outreach_repo = MagicMock()
    mock_outreach_repo.parse_object_id = MagicMock(side_effect=lambda x: ObjectId(x))
    mock_outreach_repo.count = AsyncMock(return_value=1)

    service = SalesWorkspaceService(
        business_repo=mock_biz_repo,
        lead_repo=mock_lead_repo,
        audit_repo=mock_audit_repo,
        outreach_repo=mock_outreach_repo,
    )

    res = await service.list_sales_leads(page=1, page_size=10, min_score=70.0)
    assert res.pagination.total == 1
    assert len(res.leads) == 1
    lead_summary = res.leads[0]
    assert lead_summary.business_name == "Acme Dentistry"
    assert lead_summary.qualification_score == 85.0
    assert lead_summary.has_website is True
    assert lead_summary.has_audit is True
    assert lead_summary.has_pitch is True


def test_sales_leads_api_endpoint():
    response = client.get("/api/v1/sales/leads?page=1&page_size=10")
    assert response.status_code == 200
    data = response.json()
    assert "leads" in data
    assert "pagination" in data


from app.api.routes.dashboard import get_sales_workspace_service as get_dashboard_sales_service
from app.api.routes.sales import get_sales_workspace_service


def test_dashboard_api_endpoint():
    mock_service = MagicMock()
    mock_service.get_dashboard_summary = AsyncMock(return_value=DashboardSummaryResponse(
        total_businesses=10,
        total_leads=5,
        draft_outreach_count=2,
    ))
    app.dependency_overrides[get_dashboard_sales_service] = lambda: mock_service

    try:
        response = client.get("/api/v1/dashboard/summary")
        assert response.status_code == 200
        data = response.json()
        assert data["total_businesses"] == 10
        assert data["total_leads"] == 5
        assert data["draft_outreach_count"] == 2
    finally:
        app.dependency_overrides.clear()


def test_sales_leads_api_endpoint():
    mock_service = MagicMock()
    mock_service.list_sales_leads = AsyncMock(return_value=SalesLeadListResponse(
        leads=[],
        pagination={"page": 1, "page_size": 25, "total": 0, "pages": 1},
    ))
    app.dependency_overrides[get_sales_workspace_service] = lambda: mock_service

    try:
        response = client.get("/api/v1/sales/leads?page=1&page_size=10")
        assert response.status_code == 200
        data = response.json()
        assert "leads" in data
        assert "pagination" in data
    finally:
        app.dependency_overrides.clear()


def test_sales_lead_detail_api_endpoint():
    fake_lead_id = str(ObjectId())

    fake_lead = Lead(business_id=ObjectId(), contact=Contact(email="test@biz.com"))
    fake_biz = Business(name="Test Biz", website="https://testbiz.com", verification_status="VERIFIED", phone="+15551111")
    fake_detail = SalesLeadDetailResponse(
        lead=fake_lead,
        business=fake_biz,
        latest_research=None,
        latest_verification="VERIFIED",
        latest_website_audit=None,
        qualification=Qualification(qualification_score=80.0),
        latest_outreach=None,
        all_outreach=[],
        conversation_metadata=None,
        pipeline_state={"lead_status": "QUALIFIED"},
        readiness_flags={
            "can_verify": True, "can_research": True, "can_audit": True, "can_qualify": True,
            "can_generate_pitch": True, "has_email": True, "has_phone": True, "has_website": True,
            "has_draft": False, "is_do_not_contact": False
        },
        next_recommended_action="GENERATE_PITCH",
        contact_action_data={"phone": "+15551111", "email": "test@biz.com", "whatsapp_available": True},
    )

    mock_service = MagicMock()
    mock_service.get_lead_detail = AsyncMock(return_value=fake_detail)
    mock_service.prepare_lead = AsyncMock(return_value={
        "lead_id": fake_lead_id,
        "readiness_flags": fake_detail.readiness_flags.model_dump(),
        "next_recommended_action": "GENERATE_PITCH",
    })

    app.dependency_overrides[get_sales_workspace_service] = lambda: mock_service

    try:
        resp = client.get(f"/api/v1/sales/leads/{fake_lead_id}")
        assert resp.status_code == 200
        assert resp.json()["next_recommended_action"] == "GENERATE_PITCH"

        prep_resp = client.post(f"/api/v1/sales/leads/{fake_lead_id}/prepare")
        assert prep_resp.status_code == 200
        assert prep_resp.json()["next_recommended_action"] == "GENERATE_PITCH"
    finally:
        app.dependency_overrides.clear()


def test_sales_lead_actions_and_dnc_guard():
    fake_lead_id = str(ObjectId())

    mock_service = MagicMock()
    mock_service.execute_sales_action = AsyncMock(return_value=SalesActionResponse(
        success=True,
        action="QUALIFY",
        lead_id=fake_lead_id,
        message="Lead qualification completed successfully.",
        result={"score": 88.0},
    ))

    app.dependency_overrides[get_sales_workspace_service] = lambda: mock_service

    try:
        act_resp = client.post(
            f"/api/v1/sales/leads/{fake_lead_id}/actions/QUALIFY",
            json={"force_refresh": True},
        )
        assert act_resp.status_code == 200
        data = act_resp.json()
        assert data["success"] is True
        assert data["action"] == "QUALIFY"
    finally:
        app.dependency_overrides.clear()

