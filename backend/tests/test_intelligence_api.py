import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.enums import VerificationStatus
from app.verification.models import WebsiteFetchResult

client = TestClient(app)


@pytest.mark.asyncio
async def test_lead_intelligence_service_and_api():
    lead_id = "507f1f77bcf86cd799439022"
    biz_id = "507f1f77bcf86cd799439011"

    mock_lead_doc = {
        "_id": lead_id,
        "business_id": biz_id,
        "lead_status": "NEW",
        "pipeline_stage": "NEW",
    }
    mock_biz_doc = {
        "_id": biz_id,
        "name": "Global Solutions Ltd",
        "website": "https://globalsolutions.com",
        "normalized_domain": "globalsolutions.com",
        "phone": "+1 555 777 8888",
        "email": "contact@globalsolutions.com",
        "business_status": "ACTIVE",
        "verification_status": "UNVERIFIED",
    }

    mock_fetch = WebsiteFetchResult(
        accessible=True,
        status_code=200,
        final_url="https://globalsolutions.com",
        domain_matches=True,
        business_name_found=True,
        title="Global Solutions Ltd - Enterprise IT",
        html_content='<html><head><meta name="viewport" content="width=device-width"><title>Global Solutions Ltd</title></head><body><a href="mailto:info@globalsolutions.com">Email Us</a> quote</body></html>',
        response_time_ms=180.0,
    )

    with (
        patch("app.repositories.lead.LeadRepository.get_by_id", new_callable=AsyncMock) as mock_get_lead,
        patch("app.repositories.business.BusinessRepository.get_by_id", new_callable=AsyncMock) as mock_get_biz,
        patch("app.repositories.business.BusinessRepository.update_by_id", new_callable=AsyncMock) as mock_update_biz,
        patch("app.repositories.research.ResearchRepository.get_by_business_id", new_callable=AsyncMock) as mock_get_res,
        patch("app.repositories.research.ResearchRepository.create", new_callable=AsyncMock) as mock_create_res,
        patch("app.repositories.website_audit.WebsiteAuditRepository.create", new_callable=AsyncMock) as mock_create_audit,
        patch("app.services.agent_run.AgentRunService.create_run", new_callable=AsyncMock) as mock_create_run,
        patch("app.repositories.agent_run.AgentRunRepository.update_by_id", new_callable=AsyncMock) as mock_update_run,
        patch("app.verification.sources.website.SafeWebsiteFetcher.fetch", new_callable=AsyncMock) as mock_fetcher,
    ):
        mock_get_lead.return_value = mock_lead_doc
        mock_get_biz.return_value = mock_biz_doc
        mock_update_biz.return_value = {}
        mock_get_res.return_value = []
        mock_create_res.return_value = {
            "_id": "507f1f77bcf86cd799439099",
            "business_id": biz_id,
            "lead_id": lead_id,
            "business_summary": "Summary",
            "products_services": [],
            "research_sources": [],
            "research_version": "1.0",
        }
        mock_create_audit.return_value = {
            "_id": "507f1f77bcf86cd799439088",
            "business_id": biz_id,
            "lead_id": lead_id,
            "website_url": "https://globalsolutions.com",
            "domain": "globalsolutions.com",
            "website_exists": True,
            "overall_score": 90.0,
            "issues": [],
            "strengths": [],
            "recommendations": [],
            "audit_version": "1.0",
        }
        mock_create_run.return_value = MagicMock(id="507f1f77bcf86cd799439033")
        mock_update_run.return_value = {}
        mock_fetcher.return_value = mock_fetch

        response = client.post(f"/api/v1/leads/{lead_id}/intelligence", json={"force_refresh": True})
        assert response.status_code == 200
        data = response.json()

        assert data["lead_id"] == lead_id
        assert data["business_id"] == biz_id
        assert data["verification"]["verification_status"] == VerificationStatus.VERIFIED.value
        assert data["verification"]["website_accessible"] is True
        assert data["website_audit"]["overall_score"] == 90.0
