import pytest
from unittest.mock import AsyncMock, MagicMock

from app.auditing.checks import (
    inspect_contact_info,
    inspect_cta,
    inspect_mobile_viewport,
    run_deterministic_website_audit,
)
from app.auditing.service import WebsiteAuditService
from app.schemas.business import Business
from app.verification.models import WebsiteFetchResult


def test_audit_inspection_helpers():
    html_mobile = '<html><head><meta name="viewport" content="width=device-width"></head></html>'
    assert inspect_mobile_viewport(html_mobile) is True
    assert inspect_mobile_viewport("<html><head></head></html>") is False

    html_contact = '<html><body><a href="mailto:info@test.com">Email Us</a></body></html>'
    assert inspect_contact_info(html_contact, "Email Us") is True

    text_cta = "Click here to book a free call and get a quote now."
    assert inspect_cta(text_cta) is True


def test_audit_scoring_bounds_and_issues():
    # Test inaccessible site
    fetch_fail = WebsiteFetchResult(accessible=False, status_code=500, error_message="Internal Server Error")
    score_fail, issues_fail, _, _ = run_deterministic_website_audit("https://badsite.com", fetch_fail)
    assert score_fail <= 50.0
    assert any(i.category == "accessibility" for i in issues_fail)

    # Test accessible site with issues (no https, no viewport, slow latency)
    html = "<html><head><title>Test Site</title></head><body>Welcome to our shop</body></html>"
    fetch_slow = WebsiteFetchResult(
        accessible=True,
        status_code=200,
        final_url="http://testsite.com",
        response_time_ms=3500.0,
        title="Test Site",
        html_content=html,
    )
    score, issues, strengths, recs = run_deterministic_website_audit("http://testsite.com", fetch_slow)
    assert 0.0 <= score <= 100.0
    assert any(i.category == "security" for i in issues)
    assert any(i.category == "performance" for i in issues)
    assert any(i.category == "mobile" for i in issues)


@pytest.mark.asyncio
async def test_website_audit_service_create():
    mock_audit_repo = MagicMock()
    mock_audit_repo.parse_object_id = MagicMock(side_effect=lambda x: x)

    created_doc = {
        "_id": "507f1f77bcf86cd799439088",
        "business_id": "507f1f77bcf86cd799439011",
        "website_url": "https://testsite.com",
        "domain": "testsite.com",
        "website_exists": True,
        "overall_score": 85.0,
        "issues": [],
        "strengths": ["Site online"],
        "recommendations": [],
        "audit_version": "1.0",
    }
    mock_audit_repo.create = AsyncMock(return_value=created_doc)

    svc = WebsiteAuditService(audit_repo=mock_audit_repo)
    biz = Business(
        id="507f1f77bcf86cd799439011",
        name="Test Business",
        website="https://testsite.com",
        normalized_domain="testsite.com",
    )
    fetch_res = WebsiteFetchResult(
        accessible=True,
        final_url="https://testsite.com",
        response_time_ms=200.0,
        html_content='<html><head><meta name="viewport" content="width=device-width"><title>Test</title></head><body><a href="mailto:a@b.com">Contact</a> quote</body></html>',
        title="Test",
    )

    audit = await svc.perform_audit(business=biz, fetch_result=fetch_res)
    assert audit.overall_score == 85.0
    mock_audit_repo.create.assert_called_once()
