import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.schemas.business import Business
from app.schemas.enums import VerificationStatus
from app.verification.models import WebsiteFetchResult
from app.verification.security import validate_and_sanitize_url
from app.verification.service import VerificationService
from app.verification.validators import (
    evaluate_business_verification,
    is_valid_email,
    is_valid_phone,
)


def test_ssrf_protection_blocked_targets():
    # Loopback and private IPs
    assert validate_and_sanitize_url("http://127.0.0.1/admin")[0] is False
    assert validate_and_sanitize_url("http://localhost/secret")[0] is False
    assert validate_and_sanitize_url("http://192.168.1.1/config")[0] is False
    assert validate_and_sanitize_url("http://10.0.0.1")[0] is False
    assert validate_and_sanitize_url("http://169.254.169.254/latest/meta-data")[0] is False
    # Non HTTP schemes
    assert validate_and_sanitize_url("file:///etc/passwd")[0] is False
    assert validate_and_sanitize_url("ftp://example.com")[0] is False


def test_ssrf_protection_valid_urls():
    # Mocking socket resolution for public domain
    with patch("socket.getaddrinfo") as mock_dns:
        mock_dns.return_value = [(2, 1, 6, "", ("93.184.216.34", 443))]
        is_safe, err, sanitized = validate_and_sanitize_url("https://example.com")
        assert is_safe is True
        assert err is None
        assert sanitized.startswith("https://example.com")


def test_phone_and_email_validators():
    assert is_valid_phone("+1 555-123-4567") is True
    assert is_valid_phone("123") is False
    assert is_valid_phone(None) is False

    assert is_valid_email("contact@acme.com") is True
    assert is_valid_email("invalid-email") is False
    assert is_valid_email(None) is False


def test_verification_status_computation_verified():
    biz = Business(
        name="Acme Corp",
        website="https://acme.com",
        normalized_domain="acme.com",
        phone="+1 555 123 4567",
        email="info@acme.com",
    )
    fetch_res = WebsiteFetchResult(
        accessible=True,
        status_code=200,
        final_url="https://acme.com",
        domain_matches=True,
        business_name_found=True,
        title="Acme Corp - Main Page",
    )
    res = evaluate_business_verification(biz, fetch_res)
    assert res.verification_status == VerificationStatus.VERIFIED
    assert res.website_accessible is True
    assert res.domain_matches is True
    assert res.business_name_found is True


def test_verification_status_computation_partially_verified():
    biz = Business(
        name="Beta Logistics",
        phone="+1 555 999 8888",
        email="hello@beta.com",
    )
    res = evaluate_business_verification(biz, fetch_result=None)
    assert res.verification_status == VerificationStatus.PARTIALLY_VERIFIED
    assert res.phone_present is True
    assert res.email_present is True


def test_verification_status_computation_failed():
    biz = Business(
        name="Unknown Ghost Store",
        website="https://broken-ghost-store.com",
    )
    fetch_res = WebsiteFetchResult(
        accessible=False,
        status_code=404,
        error_message="Domain not found",
    )
    res = evaluate_business_verification(biz, fetch_res)
    assert res.verification_status == VerificationStatus.FAILED


@pytest.mark.asyncio
async def test_verification_service_flow():
    mock_biz_repo = MagicMock()
    mock_biz_repo.update_by_id = AsyncMock(return_value={})

    mock_fetcher = MagicMock()
    mock_fetcher.fetch = AsyncMock(
        return_value=WebsiteFetchResult(
            accessible=True,
            status_code=200,
            final_url="https://acme.com",
            domain_matches=True,
            business_name_found=True,
            title="Acme Corp",
        )
    )

    svc = VerificationService(business_repo=mock_biz_repo, website_fetcher=mock_fetcher)
    biz = Business(
        id="507f1f77bcf86cd799439011",
        name="Acme Corp",
        website="https://acme.com",
        normalized_domain="acme.com",
        phone="+1 555 123 4567",
        email="info@acme.com",
    )

    res, fetch_out = await svc.verify_business(biz)
    assert res.verification_status == VerificationStatus.VERIFIED
    mock_biz_repo.update_by_id.assert_called_once()
