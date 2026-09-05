import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.core.exceptions import ValidationError
from app.llm.models import LLMCompletionResponse
from app.pitch.schemas import PitchGenerationRequest
from app.pitch.service import PitchGenerationService
from app.schemas.enums import LeadStatus, OutreachChannel, OutreachMessageType, OutreachStatus


@pytest.mark.asyncio
async def test_generate_pitch_email_success():
    lead_id = "507f1f77bcf86cd799439022"
    biz_id = "507f1f77bcf86cd799439011"
    outreach_id = "507f1f77bcf86cd799439055"

    mock_lead = {"_id": lead_id, "business_id": biz_id, "lead_status": "QUALIFIED"}
    mock_biz = {"_id": biz_id, "name": "Acme Corp"}

    mock_pitch_json = {
        "channel": "EMAIL",
        "message_type": "INITIAL_PITCH",
        "subject": "Quick note regarding Acme Corp website layout",
        "body": "Hi, I noticed mobile rendering optimization opportunities...",
        "personalization_points": ["Mobile viewport missing"],
        "evidence_used": ["MOBILE_PROBLEM"],
        "recommended_service": "WEBSITE_OPTIMIZATION",
        "confidence": 0.88,
    }

    service = PitchGenerationService()

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
        mock_ctx.return_value = {"business": {"name": "Acme Corp"}}
        mock_llm_gen.return_value = LLMCompletionResponse(
            content=json.dumps(mock_pitch_json),
            model="test-model",
        )
        mock_create_out.return_value = {
            "_id": outreach_id,
            "lead_id": lead_id,
            "business_id": biz_id,
            "channel": "EMAIL",
            "direction": "OUTBOUND",
            "message_type": "INITIAL_PITCH",
            "subject": "Quick note regarding Acme Corp website layout",
            "message": "Hi, I noticed mobile rendering optimization opportunities...",
            "status": "DRAFT",
        }
        mock_create_run.return_value = MagicMock(id="507f1f77bcf86cd799439066")
        mock_update_run.return_value = {}

        req = PitchGenerationRequest(channel=OutreachChannel.EMAIL)
        res = await service.generate_pitch(lead_id, req)

        assert res.lead_id == lead_id
        assert res.outreach_id == outreach_id
        assert res.channel == OutreachChannel.EMAIL
        assert res.status == OutreachStatus.DRAFT
        assert res.subject is not None
        assert "mobile" in res.body.lower()

@pytest.mark.asyncio
async def test_generate_pitch_whatsapp_no_subject():
    lead_id = "507f1f77bcf86cd799439022"
    biz_id = "507f1f77bcf86cd799439011"
    outreach_id = "507f1f77bcf86cd799439077"

    mock_lead = {"_id": lead_id, "business_id": biz_id, "lead_status": "QUALIFIED"}

    mock_pitch_json = {
        "channel": "WHATSAPP",
        "message_type": "INITIAL_PITCH",
        "subject": "Ignored Subject",
        "body": "Hi John, quick question regarding Acme Corp's website mobile responsiveness...",
        "personalization_points": ["Mobile viewport missing"],
        "evidence_used": ["MOBILE_PROBLEM"],
        "recommended_service": "WEBSITE_OPTIMIZATION",
        "confidence": 0.85,
    }

    service = PitchGenerationService()

    with (
        patch("app.repositories.lead.LeadRepository.get_by_id", new_callable=AsyncMock) as mock_get_lead,
        patch("app.repositories.outreach.OutreachRepository.list_by_lead_id", new_callable=AsyncMock) as mock_list_out,
        patch("app.intelligence.context.LeadAIContextBuilder.build_context", new_callable=AsyncMock) as mock_ctx,
        patch("app.llm.service.LLMService.generate", new_callable=AsyncMock) as mock_llm_gen,
        patch("app.repositories.outreach.OutreachRepository.create", new_callable=AsyncMock) as mock_create_out,
        patch("app.services.agent_run.AgentRunService.create_run", new_callable=AsyncMock) as mock_create_run,
        patch("app.repositories.agent_run.AgentRunRepository.update_by_id", new_callable=AsyncMock) as mock_update_run,
    ):
        mock_get_lead.return_value = mock_lead
        mock_list_out.return_value = []
        mock_ctx.return_value = {}
        mock_llm_gen.return_value = LLMCompletionResponse(content=json.dumps(mock_pitch_json), model="test-model")
        mock_create_out.return_value = {
            "_id": outreach_id,
            "lead_id": lead_id,
            "business_id": biz_id,
            "channel": "WHATSAPP",
            "message": mock_pitch_json["body"],
            "status": "DRAFT",
        }
        mock_create_run.return_value = MagicMock(id="run123")
        mock_update_run.return_value = {}

        req = PitchGenerationRequest(channel=OutreachChannel.WHATSAPP)
        res = await service.generate_pitch(lead_id, req)

        assert res.channel == OutreachChannel.WHATSAPP
        assert res.subject is None
        assert res.status == OutreachStatus.DRAFT


@pytest.mark.asyncio
async def test_generate_pitch_duplicate_draft_reuse():
    lead_id = "507f1f77bcf86cd799439022"
    biz_id = "507f1f77bcf86cd799439011"
    existing_outreach_id = "507f1f77bcf86cd799439088"

    mock_lead = {"_id": lead_id, "business_id": biz_id, "lead_status": "QUALIFIED"}
    existing_draft = {
        "_id": existing_outreach_id,
        "lead_id": lead_id,
        "business_id": biz_id,
        "channel": "EMAIL",
        "direction": "OUTBOUND",
        "message_type": "INITIAL_PITCH",
        "subject": "Existing Subject",
        "message": "Existing draft body",
        "status": "DRAFT",
    }

    service = PitchGenerationService()

    with (
        patch("app.repositories.lead.LeadRepository.get_by_id", new_callable=AsyncMock) as mock_get_lead,
        patch("app.repositories.outreach.OutreachRepository.list_by_lead_id", new_callable=AsyncMock) as mock_list_out,
        patch("app.llm.service.LLMService.generate", new_callable=AsyncMock) as mock_llm_gen,
    ):
        mock_get_lead.return_value = mock_lead
        mock_list_out.return_value = [existing_draft]

        req = PitchGenerationRequest(channel=OutreachChannel.EMAIL, force_refresh=False)
        res = await service.generate_pitch(lead_id, req)

        assert res.outreach_id == existing_outreach_id
        assert res.body == "Existing draft body"
        mock_llm_gen.assert_not_called()


@pytest.mark.asyncio
async def test_generate_pitch_do_not_contact_blocked():
    lead_id = "507f1f77bcf86cd799439022"
    mock_lead = {"_id": lead_id, "business_id": "507f1f77bcf86cd799439011", "lead_status": "DO_NOT_CONTACT"}

    service = PitchGenerationService()

    with patch("app.repositories.lead.LeadRepository.get_by_id", new_callable=AsyncMock) as mock_get_lead:
        mock_get_lead.return_value = mock_lead
        with pytest.raises(ValidationError) as exc:
            await service.generate_pitch(lead_id)
        assert "DO_NOT_CONTACT" in str(exc.value)
