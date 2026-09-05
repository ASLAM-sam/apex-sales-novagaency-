from unittest.mock import AsyncMock, MagicMock
from bson import ObjectId
import pytest
from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.schemas.api import (
    BusinessCreateRequest,
    BusinessUpdateRequest,
    LeadCreateRequest,
    LeadUpdateRequest,
    OutreachCreateRequest,
    OutreachUpdateRequest,
    ResearchCreateRequest,
    WebsiteAuditCreateRequest,
)
from app.schemas.enums import LeadStatus, OutreachChannel, OutreachStatus, PipelineStage
from app.services.business import BusinessService
from app.services.lead import LeadService
from app.services.outreach import OutreachService
from app.services.research import ResearchService
from app.services.website_audit import WebsiteAuditService


@pytest.mark.asyncio
async def test_business_service_create_and_normalization():
    mock_repo = MagicMock()
    mock_repo.get_by_domain = AsyncMock(return_value=None)
    mock_repo.get_by_normalized_phone = AsyncMock(return_value=None)

    fake_id = ObjectId()
    mock_repo.create = AsyncMock(side_effect=lambda d: {**d, "_id": fake_id})

    service = BusinessService(business_repo=mock_repo)

    req = BusinessCreateRequest(
        name="  Test Corp  ",
        website="HTTPS://WWW.TESTCORP.COM/path",
        phone="+1 (555) 123-4567",
    )

    biz = await service.create_business(req)

    assert biz.name == "  Test Corp  "
    assert biz.normalized_name == "test corp"
    assert biz.normalized_domain == "testcorp.com"
    assert biz.normalized_phone == "15551234567"
    assert str(biz.id) == str(fake_id)


@pytest.mark.asyncio
async def test_business_service_duplicate_domain_raises_conflict():
    mock_repo = MagicMock()
    mock_repo.get_by_domain = AsyncMock(return_value={"_id": ObjectId(), "normalized_domain": "dup.com"})

    service = BusinessService(business_repo=mock_repo)

    req = BusinessCreateRequest(
        name="Dup Corp",
        website="https://dup.com",
    )

    with pytest.raises(ConflictError) as exc_info:
        await service.create_business(req)

    assert "already exists" in str(exc_info.value.message)


@pytest.mark.asyncio
async def test_lead_service_create_missing_business_raises_404():
    mock_lead_repo = MagicMock()
    mock_biz_repo = MagicMock()
    mock_biz_repo.get_by_id = AsyncMock(return_value=None)

    service = LeadService(lead_repo=mock_lead_repo, business_repo=mock_biz_repo)

    fake_biz_id = str(ObjectId())
    req = LeadCreateRequest(business_id=fake_biz_id)

    with pytest.raises(NotFoundError) as exc_info:
        await service.create_lead(req)

    assert f"business with ID '{fake_biz_id}' not found" in str(exc_info.value.message)


@pytest.mark.asyncio
async def test_lead_service_create_and_defaults():
    mock_lead_repo = MagicMock()
    fake_biz_oid = ObjectId()
    mock_lead_repo.parse_object_id = lambda x: ObjectId(x)

    mock_biz_repo = MagicMock()
    mock_biz_repo.get_by_id = AsyncMock(return_value={"_id": fake_biz_oid, "name": "Biz"})

    fake_lead_oid = ObjectId()
    mock_lead_repo.create = AsyncMock(side_effect=lambda d: {**d, "_id": fake_lead_oid})

    service = LeadService(lead_repo=mock_lead_repo, business_repo=mock_biz_repo)

    req = LeadCreateRequest(business_id=str(fake_biz_oid))
    lead = await service.create_lead(req)

    assert str(lead.id) == str(fake_lead_oid)
    assert str(lead.business_id) == str(fake_biz_oid)
    assert lead.lead_status == LeadStatus.NEW
    assert lead.pipeline_stage == PipelineStage.NEW


@pytest.mark.asyncio
async def test_outreach_service_prevents_unsafe_sent_transition():
    mock_outreach_repo = MagicMock()
    fake_outreach_id = str(ObjectId())

    mock_outreach_repo.get_by_id = AsyncMock(
        return_value={
            "_id": ObjectId(fake_outreach_id),
            "lead_id": ObjectId(),
            "business_id": ObjectId(),
            "channel": OutreachChannel.EMAIL,
            "status": OutreachStatus.DRAFT,
            "message": "Hello",
        }
    )

    service = OutreachService(outreach_repo=mock_outreach_repo)

    req = OutreachUpdateRequest(status=OutreachStatus.SENT)

    with pytest.raises(ValidationError) as exc_info:
        await service.update_outreach(fake_outreach_id, req)

    assert "Direct transition to status 'SENT' is not permitted" in str(exc_info.value.message)


@pytest.mark.asyncio
async def test_outreach_service_allows_ready_transition():
    mock_outreach_repo = MagicMock()
    fake_outreach_id = str(ObjectId())

    existing_doc = {
        "_id": ObjectId(fake_outreach_id),
        "lead_id": ObjectId(),
        "business_id": ObjectId(),
        "channel": OutreachChannel.EMAIL,
        "status": OutreachStatus.DRAFT,
        "message": "Hello",
    }
    mock_outreach_repo.get_by_id = AsyncMock(return_value=existing_doc)
    mock_outreach_repo.update_by_id = AsyncMock(
        return_value={**existing_doc, "status": OutreachStatus.READY}
    )

    service = OutreachService(outreach_repo=mock_outreach_repo)

    req = OutreachUpdateRequest(status=OutreachStatus.READY)
    updated = await service.update_outreach(fake_outreach_id, req)

    assert updated.status == OutreachStatus.READY
