import pytest
from unittest.mock import AsyncMock, MagicMock
from bson import ObjectId
from fastapi.testclient import TestClient

from app.acquisition.exceptions import UnsupportedAcquisitionSourceError
from app.acquisition.schemas import (
    AcquisitionCandidateInput,
    AcquisitionImportRequest,
    AcquisitionSearchRequest,
)
from app.acquisition.service import LeadAcquisitionService
from app.main import app

client = TestClient(app)


@pytest.mark.asyncio
async def test_acquisition_manual_search_empty():
    service = LeadAcquisitionService()
    req = AcquisitionSearchRequest(source="manual", manual_candidates=[])
    res = await service.search(req)
    assert res.total == 0
    assert res.candidates == []
    assert res.source == "manual"


@pytest.mark.asyncio
async def test_acquisition_invalid_source_raises_error():
    service = LeadAcquisitionService()
    req = AcquisitionSearchRequest(source="unsupported_source_xyz")
    with pytest.raises(UnsupportedAcquisitionSourceError):
        await service.search(req)


@pytest.mark.asyncio
async def test_acquisition_candidate_normalization_and_deduplication():
    mock_biz_repo = MagicMock()
    mock_biz_repo.get_by_domain = AsyncMock(return_value=None)
    mock_biz_repo.get_by_normalized_phone = AsyncMock(return_value=None)
    mock_biz_repo.get_by_normalized_name = AsyncMock(return_value=None)

    mock_lead_repo = MagicMock()

    service = LeadAcquisitionService(
        business_repo=mock_biz_repo,
        lead_repo=mock_lead_repo,
    )

    candidates = [
        AcquisitionCandidateInput(
            name="  Apex Tech Corp  ",
            website="https://www.apextech.com/about",
            phone="+1 555-0199",
            email="info@apextech.com",
            city="San Francisco",
        ),
        AcquisitionCandidateInput(
            name="Apex Tech Duplicate",
            website="http://apextech.com",
            phone="+1 555-0199",
        ),
    ]

    req = AcquisitionSearchRequest(source="manual", manual_candidates=candidates)
    res = await service.search(req)

    assert res.total == 1
    cand = res.candidates[0]
    assert cand.name == "Apex Tech Corp"
    assert cand.website == "https://apextech.com"
    assert cand.phone == "+1 555-0199"
    assert cand.email == "info@apextech.com"
@pytest.mark.asyncio
async def test_acquisition_existing_business_and_lead_detection():
    fake_biz_id = str(ObjectId())
    fake_lead_id = str(ObjectId())

    mock_biz_repo = MagicMock()
    mock_biz_repo.get_by_domain = AsyncMock(return_value={
        "_id": ObjectId(fake_biz_id),
        "name": "Existing Dental LLC",
        "normalized_domain": "existingdental.com",
    })

    mock_lead_repo = MagicMock()
    mock_lead_repo.find_by_business_id = AsyncMock(return_value=[{
        "_id": ObjectId(fake_lead_id),
        "lead_status": "QUALIFIED",
        "qualification": {"qualification_status": "HIGH"},
    }])

    service = LeadAcquisitionService(
        business_repo=mock_biz_repo,
        lead_repo=mock_lead_repo,
    )

    req = AcquisitionSearchRequest(
        source="manual",
        manual_candidates=[
            AcquisitionCandidateInput(
                name="Existing Dental",
                website="https://existingdental.com",
            )
        ],
    )
    res = await service.search(req)

    assert res.total == 1
    cand = res.candidates[0]
    assert cand.already_exists is True
    assert cand.existing_business_id == fake_biz_id
    assert cand.existing_lead_id == fake_lead_id
    assert cand.qualification_state == "HIGH"


@pytest.mark.asyncio
async def test_acquisition_import_success_and_dnc_protection():
    fake_biz_id = str(ObjectId())
    fake_dnc_lead_id = str(ObjectId())

    mock_biz_repo = MagicMock()
    mock_biz_repo.get_by_domain = AsyncMock(return_value={
        "_id": ObjectId(fake_biz_id),
        "normalized_domain": "dnc-clinic.com",
    })

    mock_lead_repo = MagicMock()
    mock_lead_repo.find_by_business_id = AsyncMock(return_value=[{
        "_id": ObjectId(fake_dnc_lead_id),
        "lead_status": "DO_NOT_CONTACT",
    }])

    mock_biz_service = MagicMock()
    mock_lead_service = MagicMock()

    service = LeadAcquisitionService(
        business_repo=mock_biz_repo,
        lead_repo=mock_lead_repo,
        business_service=mock_biz_service,
        lead_service=mock_lead_service,
    )

    import_req = AcquisitionImportRequest(
        candidates=[
            AcquisitionCandidateInput(
                name="DNC Clinic",
                website="https://dnc-clinic.com",
            ),
            AcquisitionCandidateInput(name=""),
        ]
    )

    res = await service.import_candidates(import_req)
    assert res.imported == 0
    assert res.already_exists == 1
    assert res.invalid == 1
    assert mock_lead_service.create_lead.call_count == 0


@pytest.mark.asyncio
async def test_acquisition_search_never_creates_leads_or_businesses():
    """
    Phase 15 invariant: SEARCH must not write. It only normalizes, deduplicates,
    and checks existing businesses/leads.
    """
    mock_biz_repo = MagicMock()
    mock_biz_repo.get_by_domain = AsyncMock(return_value=None)
    mock_biz_repo.get_by_normalized_phone = AsyncMock(return_value=None)
    mock_biz_repo.get_by_normalized_name = AsyncMock(return_value=None)

    mock_lead_repo = MagicMock()
    mock_lead_repo.find_by_business_id = AsyncMock(return_value=[])

    mock_biz_service = MagicMock()
    mock_lead_service = MagicMock()

    service = LeadAcquisitionService(
        business_repo=mock_biz_repo,
        lead_repo=mock_lead_repo,
        business_service=mock_biz_service,
        lead_service=mock_lead_service,
    )

    req = AcquisitionSearchRequest(
        source="manual",
        manual_candidates=[
            AcquisitionCandidateInput(
                name="Fresh Corner Cafe",
                website="https://freshcornercafe.com",
                phone="+1 555 0100",
                city="Austin",
            )
        ],
    )
    res = await service.search(req)

    assert res.total == 1
    assert res.candidates[0].already_exists is False

    # Search must never trigger persistence side effects.
    mock_biz_service.create_business.assert_not_called()
    mock_lead_service.create_lead.assert_not_called()
    mock_biz_repo.create.assert_not_called()
    mock_lead_repo.create.assert_not_called()


@pytest.mark.asyncio
async def test_acquisition_import_selected_candidate_creates_lead():
    """
    Phase 15 invariant: IMPORT of selected candidates creates Business + Lead
    records through the service layer (never in the route).
    """
    mock_biz_repo = MagicMock()
    mock_biz_repo.get_by_domain = AsyncMock(return_value=None)
    mock_biz_repo.get_by_normalized_phone = AsyncMock(return_value=None)
    mock_biz_repo.get_by_normalized_name = AsyncMock(return_value=None)

    mock_lead_repo = MagicMock()
    mock_lead_repo.find_by_business_id = AsyncMock(return_value=[])

    created_biz = MagicMock()
    created_biz.id = ObjectId()
    mock_biz_service = MagicMock()
    mock_biz_service.create_business = AsyncMock(return_value=created_biz)

    created_lead = MagicMock()
    created_lead.id = ObjectId()
    mock_lead_service = MagicMock()
    mock_lead_service.create_lead = AsyncMock(return_value=created_lead)

    service = LeadAcquisitionService(
        business_repo=mock_biz_repo,
        lead_repo=mock_lead_repo,
        business_service=mock_biz_service,
        lead_service=mock_lead_service,
    )

    import_req = AcquisitionImportRequest(
        candidates=[
            AcquisitionCandidateInput(
                name="Sunny Bakery",
                website="https://sunnybakery.com",
                phone="+1 555 0198",
                email="hello@sunnybakery.com",
                city="Denver",
                category="Bakery",
            )
        ]
    )

    res = await service.import_candidates(import_req)

    assert res.imported == 1
    assert res.already_exists == 0
    assert res.duplicates == 0
    assert res.invalid == 0
    assert res.failed == 0
    assert len(res.business_ids) == 1
    assert len(res.lead_ids) == 1
    assert res.details[0]["status"] == "imported"

    mock_biz_service.create_business.assert_awaited_once()
    mock_lead_service.create_lead.assert_awaited_once()


@pytest.mark.asyncio
async def test_acquisition_import_duplicates_handled_by_backend():
    """
    Phase 15 invariant: backend deduplication must catch duplicates within a
    single import batch without creating duplicate leads.
    """
    mock_biz_repo = MagicMock()
    mock_biz_repo.get_by_domain = AsyncMock(return_value=None)
    mock_biz_repo.get_by_normalized_phone = AsyncMock(return_value=None)
    mock_biz_repo.get_by_normalized_name = AsyncMock(return_value=None)

    mock_lead_repo = MagicMock()
    mock_lead_repo.find_by_business_id = AsyncMock(return_value=[])

    created_biz = MagicMock()
    created_biz.id = ObjectId()
    mock_biz_service = MagicMock()
    mock_biz_service.create_business = AsyncMock(return_value=created_biz)

    created_lead = MagicMock()
    created_lead.id = ObjectId()
    mock_lead_service = MagicMock()
    mock_lead_service.create_lead = AsyncMock(return_value=created_lead)

    service = LeadAcquisitionService(
        business_repo=mock_biz_repo,
        lead_repo=mock_lead_repo,
        business_service=mock_biz_service,
        lead_service=mock_lead_service,
    )

    import_req = AcquisitionImportRequest(
        candidates=[
            AcquisitionCandidateInput(name="Dupe Workshop", website="https://dupeworkshop.com"),
            AcquisitionCandidateInput(name="Dupe Workshop Copy", website="http://dupeworkshop.com"),
        ]
    )

    res = await service.import_candidates(import_req)

    assert res.imported == 1
    assert res.duplicates == 1
    assert len(res.lead_ids) == 1
    mock_biz_service.create_business.assert_awaited_once()
    mock_lead_service.create_lead.assert_awaited_once()


from app.api.routes.acquisition import get_acquisition_service


def test_acquisition_api_search_and_import_endpoints():
    mock_service = MagicMock()
    mock_service.search = AsyncMock(return_value=MagicMock(
        total=1,
        source="manual",
        candidates=[
            {
                "candidate_id": "c1",
                "name": "API Test Cafe",
                "website": "https://testcafe.com",
                "phone": "+1 555 4321",
                "category": "Restaurant",
                "city": "Austin",
                "source": "manual",
                "already_exists": False,
            }
        ],
    ))
    mock_service.import_candidates = AsyncMock(return_value=MagicMock(
        imported=1,
        already_exists=0,
        duplicates=0,
        invalid=0,
        failed=0,
        business_ids=["biz_123"],
        lead_ids=["lead_123"],
        details=[{"status": "imported"}],
    ))

    app.dependency_overrides[get_acquisition_service] = lambda: mock_service

    try:
        search_payload = {
            "source": "manual",
            "limit": 10,
            "manual_candidates": [
                {
                    "name": "API Test Cafe",
                    "website": "https://testcafe.com",
                    "phone": "+1 555 4321",
                    "category": "Restaurant",
                    "city": "Austin",
                }
            ],
        }
        response = client.post("/api/v1/acquisition/search", json=search_payload)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1

        import_payload = {
            "candidates": [
                {
                    "name": "API Test Cafe",
                    "website": "https://testcafe.com",
                    "phone": "+1 555 4321",
                    "category": "Restaurant",
                    "city": "Austin",
                }
            ]
        }

        imp_resp = client.post("/api/v1/acquisition/import", json=import_payload)
        assert imp_resp.status_code == 200
        imp_data = imp_resp.json()
        assert imp_data["imported"] == 1
        assert imp_data["business_ids"] == ["biz_123"]
    finally:
        app.dependency_overrides.clear()
