import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient

from app.discovery.deduplicator import CandidateDeduplicator
from app.discovery.exceptions import UnsupportedDiscoverySourceError
from app.discovery.models import DiscoveredCandidate
from app.discovery.normalizer import CandidateNormalizer
from app.discovery.schemas import DiscoverySearchRequest
from app.discovery.service import DiscoveryService
from app.discovery.sources.manual import ManualDiscoverySource
from app.main import app


# -----------------------------------------------------------------------------
# 1. Request Validation Tests
# -----------------------------------------------------------------------------
def test_discovery_request_defaults():
    req = DiscoverySearchRequest()
    assert req.source == "manual"
    assert req.max_results == 25
    assert req.query is None
    assert req.location is None


def test_discovery_request_max_results_bounds():
    with pytest.raises(Exception):
        DiscoverySearchRequest(max_results=0)

    with pytest.raises(Exception):
        DiscoverySearchRequest(max_results=1000)

    req_ok = DiscoverySearchRequest(max_results=100)
    assert req_ok.max_results == 100


# -----------------------------------------------------------------------------
# 2. Candidate Normalizer Tests
# -----------------------------------------------------------------------------
def test_normalizer_name():
    raw, norm = CandidateNormalizer.normalize_name("  Acme  Corp,   Inc.  ")
    assert raw == "Acme Corp, Inc."
    assert norm == "acme corp, inc."


def test_normalizer_domain():
    url1, domain1 = CandidateNormalizer.normalize_domain("https://www.example.com/path?q=1")
    assert domain1 == "example.com"
    assert url1 == "https://example.com"

    url2, domain2 = CandidateNormalizer.normalize_domain("http://blog.company.co.uk/")
    assert domain2 == "blog.company.co.uk"
    assert url2 == "http://blog.company.co.uk"

    url3, domain3 = CandidateNormalizer.normalize_domain("invalid-domain")
    assert domain3 is None
    assert url3 is None


def test_normalizer_phone():
    raw, norm = CandidateNormalizer.normalize_phone("+1 (555) 019-2831")
    assert norm == "+15550192831"

    raw2, norm2 = CandidateNormalizer.normalize_phone("022 1234 5678")
    assert norm2 == "02212345678"

    raw3, norm3 = CandidateNormalizer.normalize_phone("123")
    assert norm3 is None


def test_normalizer_email():
    assert CandidateNormalizer.normalize_email("  Test.User@Example.COM ") == "test.user@example.com"
    assert CandidateNormalizer.normalize_email("invalid-email") is None


def test_normalizer_rejects_empty_candidate():
    empty_cand = DiscoveredCandidate(name="   ", website=None, phone=None)
    norm = CandidateNormalizer.normalize_candidate(empty_cand)
    assert norm is None


# -----------------------------------------------------------------------------
# 3. Manual Discovery Source Tests
# -----------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_manual_source_search():
    source = ManualDiscoverySource()
    req = DiscoverySearchRequest(
        manual_candidates=[
            {"name": "Tech Solutions", "website": "https://tech.com", "phone": "1234567890"},
            {"business_name": "Cafe Mocha", "city": "Mumbai"},
            "invalid_non_dict_candidate",
        ]
    )
    candidates = await source.search(req)
    assert len(candidates) == 2
    assert candidates[0].name == "Tech Solutions"
    assert candidates[0].website == "https://tech.com"
    assert candidates[1].name == "Cafe Mocha"
    assert candidates[1].city == "Mumbai"


# -----------------------------------------------------------------------------
# 4. Deduplicator Unit Tests
# -----------------------------------------------------------------------------
def test_batch_deduplication():
    dedup = CandidateDeduplicator(business_repo=MagicMock())
    c1 = CandidateNormalizer.normalize_candidate(
        DiscoveredCandidate(name="Alpha Corp", website="alpha.com", phone="1112223333", city="Chicago")
    )
    c2_dup_domain = CandidateNormalizer.normalize_candidate(
        DiscoveredCandidate(name="Alpha Branch", website="https://alpha.com", phone="9998887777")
    )
    c3_dup_phone = CandidateNormalizer.normalize_candidate(
        DiscoveredCandidate(name="Beta Inc", website="beta.com", phone="1112223333")
    )

    assert dedup.is_batch_duplicate(c1) is False
    assert dedup.is_batch_duplicate(c2_dup_domain) is True
    assert dedup.is_batch_duplicate(c3_dup_phone) is True


# -----------------------------------------------------------------------------
# 5. Discovery Service Integration Tests (Mocked DB Repositories)
# -----------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_discovery_service_flow():
    created_biz_doc = {
        "_id": "507f1f77bcf86cd799439011",
        "name": "Global Traders",
        "normalized_domain": "globaltraders.com",
        "business_status": "ACTIVE",
        "verification_status": "UNVERIFIED",
    }
    mock_biz_repo = MagicMock()
    mock_biz_repo.get_by_id = AsyncMock(return_value=created_biz_doc)
    mock_biz_repo.get_by_domain = AsyncMock(return_value=None)
    mock_biz_repo.get_by_normalized_phone = AsyncMock(return_value=None)
    mock_biz_repo.get_by_normalized_name = AsyncMock(return_value=None)
    mock_biz_repo.create = AsyncMock(return_value=created_biz_doc)

    mock_lead_repo = MagicMock()
    mock_lead_repo.find_by_business_id = AsyncMock(return_value=[])
    mock_lead_repo.parse_object_id = MagicMock(side_effect=lambda x: x)

    created_lead_doc = {
        "_id": "507f1f77bcf86cd799439022",
        "business_id": "507f1f77bcf86cd799439011",
        "lead_status": "NEW",
        "pipeline_stage": "NEW",
    }
    mock_lead_repo.create = AsyncMock(return_value=created_lead_doc)

    mock_agent_run_service = MagicMock()
    mock_agent_run_service.create_run = AsyncMock(
        return_value=MagicMock(id="507f1f77bcf86cd799439033")
    )
    mock_agent_run_service.run_repo.update_by_id = AsyncMock(return_value={})

    service = DiscoveryService(
        business_repo=mock_biz_repo,
        lead_repo=mock_lead_repo,
        agent_run_service=mock_agent_run_service,
    )

    req = DiscoverySearchRequest(
        source="manual",
        manual_candidates=[
            {
                "name": "Global Traders",
                "website": "https://globaltraders.com",
                "phone": "+1234567890",
                "city": "New York",
            }
        ],
    )

    resp = await service.discover(req)

    assert resp.data.requested == 1
    assert resp.data.received == 1
    assert resp.data.valid == 1
    assert resp.data.duplicates == 0
    assert resp.data.new_businesses == 1
    assert resp.data.new_leads == 1
    assert "507f1f77bcf86cd799439011" in resp.data.created_business_ids
    assert "507f1f77bcf86cd799439022" in resp.data.created_lead_ids


@pytest.mark.asyncio
async def test_discovery_service_existing_business_conservative_merge():
    existing_biz_doc = {
        "_id": "507f1f77bcf86cd799439011",
        "name": "Apex Logistics",
        "normalized_name": "apex logistics",
        "normalized_domain": "apexlogistics.com",
        "website": "https://apexlogistics.com",
        "phone": "+19998887777",
        "email": None,
        "address": None,
    }

    mock_biz_repo = MagicMock()
    mock_biz_repo.get_by_id = AsyncMock(return_value=existing_biz_doc)
    mock_biz_repo.get_by_domain = AsyncMock(return_value=existing_biz_doc)
    mock_biz_repo.get_by_normalized_phone = AsyncMock(return_value=None)
    mock_biz_repo.get_by_normalized_name = AsyncMock(return_value=None)
    mock_biz_repo.update_by_id = AsyncMock(return_value=existing_biz_doc)

    mock_lead_repo = MagicMock()
    mock_lead_repo.find_by_business_id = AsyncMock(
        return_value=[{"_id": "507f1f77bcf86cd799439022", "business_id": "507f1f77bcf86cd799439011"}]
    )

    mock_agent_run_service = MagicMock()
    mock_agent_run_service.create_run = AsyncMock(return_value=MagicMock(id=None))

    service = DiscoveryService(
        business_repo=mock_biz_repo,
        lead_repo=mock_lead_repo,
        agent_run_service=mock_agent_run_service,
    )

    req = DiscoverySearchRequest(
        source="manual",
        manual_candidates=[
            {
                "name": "Apex Logistics",
                "website": "https://apexlogistics.com",
                "phone": "+10000000000",
                "email": "contact@apexlogistics.com",
            }
        ],
    )

    resp = await service.discover(req)

    assert resp.data.received == 1
    assert resp.data.valid == 1
    assert resp.data.existing_businesses == 1
    assert resp.data.new_businesses == 0
    assert resp.data.new_leads == 0

    mock_biz_repo.update_by_id.assert_called()
    update_call_args = mock_biz_repo.update_by_id.call_args[0][1]
    assert "email" in update_call_args
    assert "phone" not in update_call_args


@pytest.mark.asyncio
async def test_discovery_service_unsupported_source():
    service = DiscoveryService()
    req = DiscoverySearchRequest(source="unsupported_source_xyz")

    with pytest.raises(UnsupportedDiscoverySourceError):
        await service.discover(req)


# -----------------------------------------------------------------------------
# 6. API Route Tests (FastAPI TestClient)
# -----------------------------------------------------------------------------
def test_api_discovery_search_empty_manual_candidates():
    client = TestClient(app)
    response = client.post(
        "/api/v1/discovery/search",
        json={"source": "manual", "manual_candidates": [], "max_results": 10},
    )
    assert response.status_code == 200
    res_data = response.json()
    assert "data" in res_data
    assert res_data["data"]["source"] == "manual"
    assert res_data["data"]["received"] == 0
    assert res_data["data"]["valid"] == 0


def test_api_discovery_search_invalid_max_results():
    client = TestClient(app)
    response = client.post(
        "/api/v1/discovery/search",
        json={"source": "manual", "max_results": 500},
    )
    assert response.status_code == 422


def test_api_discovery_search_unsupported_source():
    client = TestClient(app)
    response = client.post(
        "/api/v1/discovery/search",
        json={"source": "unknown_provider"},
    )
    assert response.status_code == 400
    assert "not supported" in response.json()["detail"].lower()
