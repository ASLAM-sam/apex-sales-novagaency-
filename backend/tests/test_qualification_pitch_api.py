import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.llm.models import LLMCompletionResponse

client = TestClient(app)


@pytest.mark.asyncio
async def test_qualify_lead_api_endpoint():
    lead_id = "507f1f77bcf86cd799439022"
    biz_id = "507f1f77bcf86cd799439011"

    mock_lead = {"_id": lead_id, "business_id": biz_id, "lead_status": "NEW"}
    mock_biz = {"_id": biz_id, "name": "Acme Corp"}

    mock_qual_json = {
        "qualification_score": 85.0,
        "qualification_label": "HIGH",
        "confidence": 0.90,
        "recommended_services": [
            {
                "service": "WEBSITE_REDESIGN",
                "reason": "Mobile viewport missing.",
                "confidence": 0.90,
                "evidence": ["MOBILE_PROBLEM"],
            }
        ],
        "reasons": ["Mobile layout issue detected"],
        "positive_signals": ["Verified business"],
        "negative_signals": ["Mobile problem"],
        "evidence": ["MOBILE_PROBLEM"],
        "risks": [],
        "summary": "High opportunity lead.",
    }

    with (
        patch("app.repositories.lead.LeadRepository.get_by_id", new_callable=AsyncMock) as mock_get_lead,
        patch("app.repositories.business.BusinessRepository.get_by_id", new_callable=AsyncMock) as mock_get_biz,
        patch("app.intelligence.context.LeadAIContextBuilder.build_context", new_callable=AsyncMock) as mock_ctx,
        patch("app.llm.service.LLMService.generate", new_callable=AsyncMock) as mock_llm_gen,
        patch("app.services.agent_run.AgentRunService.create_run", new_callable=AsyncMock) as mock_create_run,
        patch("app.repositories.agent_run.AgentRunRepository.update_by_id", new_callable=AsyncMock) as mock_update_run,
        patch("app.repositories.lead.LeadRepository.update_by_id", new_callable=AsyncMock) as mock_update_lead,
    ):
        mock_get_lead.return_value = mock_lead
        mock_get_biz.return_value = mock_biz
        mock_ctx.return_value = {}
        mock_llm_gen.return_value = LLMCompletionResponse(content=json.dumps(mock_qual_json), model="test-model")
        mock_create_run.return_value = MagicMock(id="507f1f77bcf86cd799439044")
        mock_update_run.return_value = {}
        mock_update_lead.return_value = {}

        response = client.post(f"/api/v1/leads/{lead_id}/qualify", json={"force_refresh": True})
        assert response.status_code == 200
        data = response.json()
        assert data["lead_id"] == lead_id
        assert data["qualification"]["qualification_score"] == 85.0
        assert data["qualification"]["qualification_label"] == "HIGH"


@pytest.mark.asyncio
async def test_generate_pitch_api_endpoint():
    lead_id = "507f1f77bcf86cd799439022"
    biz_id = "507f1f77bcf86cd799439011"
    outreach_id = "507f1f77bcf86cd799439055"

    mock_lead = {"_id": lead_id, "business_id": biz_id, "lead_status": "QUALIFIED"}
    mock_biz = {"_id": biz_id, "name": "Acme Corp"}

    mock_pitch_json = {
        "channel": "EMAIL",
        "message_type": "INITIAL_PITCH",
        "subject": "Improving Acme Corp mobile layout",
        "body": "Hi Acme team, observed mobile viewport optimization opportunity.",
        "personalization_points": ["Mobile viewport missing"],
        "evidence_used": ["MOBILE_PROBLEM"],
        "recommended_service": "WEBSITE_OPTIMIZATION",
        "confidence": 0.88,
    }

    with (
        patch("app.repositories.lead.LeadRepository.get_by_id", new_callable=AsyncMock) as mock_get_lead,
        patch("app.repositories.business.BusinessRepository.get_by_id", new_callable=AsyncMock) as mock_get_biz,
        patch("app.repositories.outreach.OutreachRepository.list_by_lead_id", new_callable=AsyncMock) as mock_list_out,
        patch("app.intelligence.context.LeadAIContextBuilder.build_context", new_callable=AsyncMock) as mock_ctx,
        patch("app.llm.service.LLMService.generate", new_callable=AsyncMock) as mock_llm_gen,
        patch("app.repositories.outreach.OutreachRepository.create", new_callable=AsyncMock) as mock_create_out,
        patch("app.services.agent_run.AgentRunService.create_run", new_callable=AsyncMock) as mock_create_run,
        patch("app.repositories.agent_run.AgentRunRepository.update_by_id", new_callable=AsyncMock) as mock_update_run,
    ):
        mock_get_lead.return_value = mock_lead
        mock_get_biz.return_value = mock_biz
        mock_list_out.return_value = []
        mock_ctx.return_value = {}
        mock_llm_gen.return_value = LLMCompletionResponse(content=json.dumps(mock_pitch_json), model="test-model")
        mock_create_out.return_value = {
            "_id": outreach_id,
            "lead_id": lead_id,
            "business_id": biz_id,
            "channel": "EMAIL",
            "direction": "OUTBOUND",
            "message_type": "INITIAL_PITCH",
            "subject": "Improving Acme Corp mobile layout",
            "message": "Hi Acme team...",
            "status": "DRAFT",
        }
        mock_create_run.return_value = MagicMock(id="507f1f77bcf86cd799439066")
        mock_update_run.return_value = {}

        response = client.post(
            f"/api/v1/leads/{lead_id}/pitch",
            json={"channel": "EMAIL", "message_type": "INITIAL_PITCH"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["lead_id"] == lead_id
        assert data["outreach_id"] == outreach_id
        assert data["status"] == "DRAFT"
