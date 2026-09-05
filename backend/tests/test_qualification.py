import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.core.exceptions import ValidationError
from app.intelligence.context import LeadAIContextBuilder
from app.llm.models import LLMCompletionResponse
from app.qualification.schemas import LeadQualificationRequest, OpportunityLabel
from app.qualification.service import LeadQualificationService
from app.schemas.enums import LeadStatus


@pytest.mark.asyncio
async def test_lead_context_builder():
    lead_id = "507f1f77bcf86cd799439022"
    biz_id = "507f1f77bcf86cd799439011"

    mock_lead = {
        "_id": lead_id,
        "business_id": biz_id,
        "lead_status": "NEW",
        "contact": {"name": "Alice Smith", "email": "alice@acme.com"},
    }
    mock_biz = {
        "_id": biz_id,
        "name": "Acme Corp",
        "website": "https://acme.com",
        "category": "Retail",
        "phone": "+15551234567",
        "email": "contact@acme.com",
        "city": "Seattle",
        "state": "WA",
        "country": "USA",
        "business_status": "ACTIVE",
        "verification_status": "VERIFIED",
    }

    builder = LeadAIContextBuilder()

    with (
        patch("app.repositories.lead.LeadRepository.get_by_id", new_callable=AsyncMock) as mock_get_lead,
        patch("app.repositories.business.BusinessRepository.get_by_id", new_callable=AsyncMock) as mock_get_biz,
        patch("app.repositories.research.ResearchRepository.get_by_lead_id", new_callable=AsyncMock) as mock_get_res,
        patch("app.repositories.research.ResearchRepository.get_by_business_id", new_callable=AsyncMock) as mock_get_res_biz,
        patch("app.repositories.website_audit.WebsiteAuditRepository.get_latest_for_business", new_callable=AsyncMock) as mock_get_audit,
        patch("app.repositories.website_audit.WebsiteAuditRepository.get_by_lead_id", new_callable=AsyncMock) as mock_get_audit_lead,
    ):
        mock_get_lead.return_value = mock_lead
        mock_get_biz.return_value = mock_biz
        mock_get_res.return_value = []
        mock_get_res_biz.return_value = []
        mock_get_audit.return_value = None
        mock_get_audit_lead.return_value = []

        ctx = await builder.build_context(lead_id)
        assert ctx["business"]["name"] == "Acme Corp"
        assert ctx["verification"]["verification_status"] == "VERIFIED"
        assert ctx["lead"]["contact_name"] == "Alice Smith"
@pytest.mark.asyncio
async def test_qualify_lead_success():
    lead_id = "507f1f77bcf86cd799439022"
    biz_id = "507f1f77bcf86cd799439011"

    mock_lead = {
        "_id": lead_id,
        "business_id": biz_id,
        "lead_status": "NEW",
        "pipeline_stage": "NEW",
        "contact": {"name": "Alice Smith"},
    }
    mock_biz = {
        "_id": biz_id,
        "name": "Acme Corp",
        "website": "https://acme.com",
        "city": "Seattle",
        "business_status": "ACTIVE",
        "verification_status": "VERIFIED",
    }

    mock_llm_json = {
        "qualification_score": 82.0,
        "qualification_label": "HIGH",
        "confidence": 0.90,
        "recommended_services": [
            {
                "service": "WEBSITE_REDESIGN",
                "reason": "Mobile viewport missing and slow response time.",
                "confidence": 0.88,
                "evidence": ["MOBILE_PROBLEM"],
            }
        ],
        "reasons": ["Mobile layout issue detected", "Score is 82/100"],
        "positive_signals": ["Verified business location"],
        "negative_signals": ["Mobile viewport omitted"],
        "evidence": ["MOBILE_PROBLEM"],
        "risks": [],
        "summary": "High opportunity lead needing mobile redesign.",
    }

    service = LeadQualificationService()

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
        mock_ctx.return_value = {"business": {"name": "Acme Corp"}}
        mock_llm_gen.return_value = LLMCompletionResponse(
            content=json.dumps(mock_llm_json),
            model="test-model",
        )
        mock_create_run.return_value = MagicMock(id="507f1f77bcf86cd799439044")
        mock_update_run.return_value = {}
        mock_update_lead.return_value = {}

        res = await service.qualify_lead(lead_id, LeadQualificationRequest())

        assert res.lead_id == lead_id
        assert res.qualification.qualification_score == 82.0
        assert res.qualification.qualification_label == OpportunityLabel.HIGH
        assert len(res.qualification.recommended_services) == 1
        assert res.qualification.recommended_services[0].service == "WEBSITE_REDESIGN"


@pytest.mark.asyncio
async def test_qualify_lead_do_not_contact_blocked():
    lead_id = "507f1f77bcf86cd799439022"
    mock_lead = {
        "_id": lead_id,
        "business_id": "507f1f77bcf86cd799439011",
        "lead_status": LeadStatus.DO_NOT_CONTACT.value,
    }

    service = LeadQualificationService()

    with patch("app.repositories.lead.LeadRepository.get_by_id", new_callable=AsyncMock) as mock_get_lead:
        mock_get_lead.return_value = mock_lead
        with pytest.raises(ValidationError) as exc:
            await service.qualify_lead(lead_id)
        assert "DO_NOT_CONTACT" in str(exc.value)


@pytest.mark.asyncio
async def test_qualify_lead_json_repair_success():
    lead_id = "507f1f77bcf86cd799439022"
    biz_id = "507f1f77bcf86cd799439011"

    mock_lead = {"_id": lead_id, "business_id": biz_id, "lead_status": "NEW"}
    mock_biz = {"_id": biz_id, "name": "Acme Corp"}

    invalid_content = "Here is the qualification: score=75, label=GOOD"
    repaired_json = {
        "qualification_score": 75.0,
        "qualification_label": "GOOD",
        "confidence": 0.80,
        "recommended_services": [],
        "reasons": ["Good lead"],
        "positive_signals": [],
        "negative_signals": [],
        "evidence": [],
        "risks": [],
        "summary": "Good opportunity.",
    }

    service = LeadQualificationService()

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
        mock_create_run.return_value = MagicMock(id="507f1f77bcf86cd799439044")
        mock_update_run.return_value = {}
        mock_update_lead.return_value = {}

        mock_llm_gen.side_effect = [
            LLMCompletionResponse(content=invalid_content, model="test-model"),
            LLMCompletionResponse(content=json.dumps(repaired_json), model="test-model"),
        ]

        res = await service.qualify_lead(lead_id)
        assert res.qualification.qualification_score == 75.0
        assert mock_llm_gen.call_count == 2
