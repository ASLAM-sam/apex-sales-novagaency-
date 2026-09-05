import re
from typing import Optional, Tuple
from app.schemas.business import Business
from app.schemas.enums import VerificationStatus
from app.verification.models import VerificationEvidenceItem, VerificationResult, WebsiteFetchResult


def is_valid_phone(phone: Optional[str]) -> bool:
    """Validate presence and basic length of phone number."""
    if not phone:
        return False
    digits = re.sub(r"\D", "", phone)
    return 7 <= len(digits) <= 15


def is_valid_email(email: Optional[str]) -> bool:
    """Validate basic structure of email address."""
    if not email:
        return False
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email.strip()))


def evaluate_business_verification(
    business: Business, fetch_result: Optional[WebsiteFetchResult] = None
) -> VerificationResult:
    """Evaluate evidence and compute deterministic VerificationStatus for a Business."""
    evidence_items = []

    # 1. Phone Evidence
    phone_present = is_valid_phone(business.phone)
    evidence_items.append(
        VerificationEvidenceItem(
            evidence_type="phone_present",
            result=phone_present,
            source="business_data",
            details=f"Phone number: {business.phone if phone_present else 'None or invalid'}",
        )
    )

    # 2. Email Evidence
    email_present = is_valid_email(business.email)
    evidence_items.append(
        VerificationEvidenceItem(
            evidence_type="email_present",
            result=email_present,
            source="business_data",
            details=f"Email address: {business.email if email_present else 'None or invalid'}",
        )
    )

    # 3. Website Evidence
    website_accessible = False
    domain_matches = False
    biz_name_found = False

    if fetch_result:
        website_accessible = fetch_result.accessible
        domain_matches = fetch_result.domain_matches
        biz_name_found = fetch_result.business_name_found

        evidence_items.append(
            VerificationEvidenceItem(
                evidence_type="website_accessible",
                result=website_accessible,
                source="website",
                details=f"Status code: {fetch_result.status_code}, Error: {fetch_result.error_message or 'None'}",
            )
        )
        evidence_items.append(
            VerificationEvidenceItem(
                evidence_type="domain_matches",
                result=domain_matches,
                source="website",
                details=f"Expected domain '{business.normalized_domain}' vs final URL '{fetch_result.final_url}'",
            )
        )
        evidence_items.append(
            VerificationEvidenceItem(
                evidence_type="business_name_found",
                result=biz_name_found,
                source="website",
                details=f"Business name '{business.name}' present in title/content: {biz_name_found}",
            )
        )
    elif business.website:
        evidence_items.append(
            VerificationEvidenceItem(
                evidence_type="website_accessible",
                result=False,
                source="website",
                details="Website fetch was not executed or failed prior to fetch.",
            )
        )

    # Status Determination Rules
    if website_accessible and domain_matches and (biz_name_found or phone_present or email_present):
        status = VerificationStatus.VERIFIED
        notes = "High confidence verification: Website accessible, domain matched, and identity confirmed."
    elif website_accessible or (phone_present and email_present) or (phone_present and business.name):
        status = VerificationStatus.PARTIALLY_VERIFIED
        notes = "Moderate confidence: Some contact or website identity verified, but missing complete match."
    elif fetch_result and not fetch_result.accessible and not phone_present and not email_present:
        status = VerificationStatus.FAILED
        notes = "Verification failed: Website unreachable and no valid phone or email contact available."
    else:
        status = VerificationStatus.UNVERIFIED
        notes = "Unverified: Insufficient evidence available to verify business identity."

    return VerificationResult(
        verification_status=status,
        business_exists_evidence=website_accessible or phone_present or email_present,
        website_accessible=website_accessible,
        domain_matches=domain_matches,
        business_name_found=biz_name_found,
        phone_present=phone_present,
        email_present=email_present,
        evidence_items=evidence_items,
        notes=notes,
    )
