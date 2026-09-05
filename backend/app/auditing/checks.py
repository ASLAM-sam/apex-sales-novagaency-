import re
from typing import List, Tuple
from app.schemas.enums import IssueSeverity
from app.schemas.website_audit import AuditIssue
from app.verification.models import WebsiteFetchResult

CTA_KEYWORDS = ["contact", "book", "call", "quote", "get started", "request", "enquire", "buy", "schedule", "demo"]
CONTACT_KEYWORDS = ["phone", "email", "contact", "address", "call us", "mail"]


def inspect_mobile_viewport(html: str) -> bool:
    return bool(html and re.search(r'<meta\s+[^>]*name=["\']viewport["\']', html, re.IGNORECASE))


def inspect_contact_info(html: str, visible_text: str) -> bool:
    if not html:
        return False
    if "mailto:" in html.lower() or "tel:" in html.lower():
        return True
    return any(kw in visible_text.lower() for kw in CONTACT_KEYWORDS)


def inspect_cta(visible_text: str) -> bool:
    return bool(visible_text and any(kw in visible_text.lower() for kw in CTA_KEYWORDS))


def run_deterministic_website_audit(
    website_url: str,
    fetch_result: WebsiteFetchResult,
) -> Tuple[float, List[AuditIssue], List[str], List[str]]:
    """Run lightweight deterministic audit checks. Returns (overall_score, issues, strengths, recommendations)."""
    score = 100.0
    issues: List[AuditIssue] = []
    strengths: List[str] = []
    recommendations: List[str] = []

    if not fetch_result.accessible:
        score -= 50.0
        issues.append(
            AuditIssue(
                category="accessibility",
                severity=IssueSeverity.CRITICAL,
                title="Website Unreachable or Inaccessible",
                description=f"HTTP request failed: {fetch_result.error_message or 'Unreachable'}.",
                evidence=f"Status: {fetch_result.status_code}, Error: {fetch_result.error_message}",
                recommendation="Fix domain DNS configuration and webserver.",
            )
        )
        recommendations.append("Ensure site is properly hosted.")
        return max(0.0, score), issues, strengths, recommendations

    strengths.append("Website is online and accessible.")

    is_https = fetch_result.final_url and fetch_result.final_url.startswith("https://")
    if not is_https:
        score -= 10.0
        issues.append(
            AuditIssue(
                category="security",
                severity=IssueSeverity.LOW,
                title="Unencrypted HTTP Connection",
                description="The website is served over insecure HTTP.",
                evidence=f"URL: {fetch_result.final_url}",
                recommendation="Install SSL certificate for HTTPS.",
            )
        )
    else:
        strengths.append("Enforces secure HTTPS connection.")

    resp_time = fetch_result.response_time_ms or 0.0
    if resp_time > 3000.0:
        score -= 20.0
        issues.append(
            AuditIssue(
                category="performance",
                severity=IssueSeverity.MEDIUM,
                title="Slow Response Time",
                description=f"Homepage latency of {resp_time:.0f}ms exceeds threshold.",
                evidence=f"Latency: {resp_time:.1f} ms",
                recommendation="Optimize server response time.",
            )
        )
    elif resp_time > 1500.0:
        score -= 10.0

    html = fetch_result.html_content or ""
    clean_text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html)).strip()

    if not fetch_result.title:
        score -= 10.0
        issues.append(
            AuditIssue(
                category="seo",
                severity=IssueSeverity.LOW,
                title="Missing Page Title",
                description="Homepage missing HTML <title> tag.",
                evidence="<title> missing",
                recommendation="Add descriptive <title> tag.",
            )
        )
    if not re.search(r'<meta\s+[^>]*name=["\']description["\']', html, re.IGNORECASE):
        score -= 10.0
        issues.append(
            AuditIssue(
                category="seo",
                severity=IssueSeverity.LOW,
                title="Missing Meta Description",
                description="Homepage lacks meta description tag.",
                evidence="<meta name='description'> missing",
                recommendation="Add meta description.",
            )
        )

    if not inspect_mobile_viewport(html):
        score -= 20.0
        issues.append(
            AuditIssue(
                category="mobile",
                severity=IssueSeverity.HIGH,
                title="Missing Mobile Viewport Configuration",
                description="No viewport meta tag found.",
                evidence="<meta name='viewport'> missing",
                recommendation="Add responsive viewport meta tag.",
            )
        )
    else:
        strengths.append("Configured with mobile viewport tag.")

    if not inspect_contact_info(html, clean_text):
        score -= 15.0
        issues.append(
            AuditIssue(
                category="conversion",
                severity=IssueSeverity.MEDIUM,
                title="Missing Visible Contact Information",
                description="No contact details found on homepage.",
                evidence="No contact details found",
                recommendation="Display contact details prominently.",
            )
        )
    else:
        strengths.append("Visible contact information present.")

    if not inspect_cta(clean_text):
        score -= 10.0
        issues.append(
            AuditIssue(
                category="conversion",
                severity=IssueSeverity.LOW,
                title="Weak Call-To-Action",
                description="No standard call-to-action terms detected.",
                evidence="No CTA terms detected",
                recommendation="Include clear CTA buttons.",
            )
        )
    else:
        strengths.append("Call-to-action wording present.")

    return round(max(0.0, min(100.0, score)), 1), issues, strengths, recommendations
