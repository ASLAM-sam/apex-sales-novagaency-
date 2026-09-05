import logging
import re
import time
from typing import Optional
from urllib.parse import urlparse
import httpx

from app.verification.models import WebsiteFetchResult
from app.verification.security import validate_and_sanitize_url

logger = logging.getLogger(__name__)

MAX_RESPONSE_BYTES = 524_288  # 500 KB limit
HTTP_TIMEOUT_SECONDS = 5.0
MAX_REDIRECTS = 3
DEFAULT_USER_AGENT = "ApexSalesAI-Bot/1.0 (+https://apexsales.ai/bot)"


def extract_title_from_html(html: str) -> Optional[str]:
    """Extract <title> content safely from raw HTML."""
    if not html:
        return None
    match = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
    if match:
        return re.sub(r"\s+", " ", match.group(1).strip())[:200]
    return None


def extract_visible_text_snippet(html: str, max_chars: int = 1000) -> str:
    """Extract plain text snippet from HTML for keyword matching."""
    if not html:
        return ""
    clean = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", html, flags=re.IGNORECASE | re.DOTALL)
    clean = re.sub(r"<[^>]+>", " ", clean)
    return re.sub(r"\s+", " ", clean).strip()[:max_chars]


class SafeWebsiteFetcher:
    """Defensive website retriever with SSRF protection and strict content caps."""

    def __init__(
        self,
        timeout: float = HTTP_TIMEOUT_SECONDS,
        max_bytes: int = MAX_RESPONSE_BYTES,
        max_redirects: int = MAX_REDIRECTS,
        user_agent: str = DEFAULT_USER_AGENT,
    ):
        self.timeout = timeout
        self.max_bytes = max_bytes
        self.max_redirects = max_redirects
        self.user_agent = user_agent

    async def fetch(
        self,
        raw_url: str,
        business_name: Optional[str] = None,
        expected_domain: Optional[str] = None,
    ) -> WebsiteFetchResult:
        is_safe, error_msg, sanitized_url = validate_and_sanitize_url(raw_url)
        if not is_safe or not sanitized_url:
            return WebsiteFetchResult(accessible=False, error_message=error_msg or "URL failed SSRF validation.")

        headers = {"User-Agent": self.user_agent, "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"}
        start_time = time.perf_counter()

        try:
            async with httpx.AsyncClient(
                timeout=self.timeout, follow_redirects=True, max_redirects=self.max_redirects, verify=False
            ) as client:
                async with client.stream("GET", sanitized_url, headers=headers) as response:
                    status_code = response.status_code
                    final_url = str(response.url)
                    headers_dict = {k.lower(): v for k, v in response.headers.items()}

                    if final_url != sanitized_url:
                        safe_redirect, redirect_err, _ = validate_and_sanitize_url(final_url)
                        if not safe_redirect:
                            return WebsiteFetchResult(
                                accessible=False,
                                status_code=status_code,
                                final_url=final_url,
                                error_message=f"Redirect blocked by SSRF: {redirect_err}",
                            )

                    content_bytes = bytearray()
                    async for chunk in response.aiter_bytes():
                        content_bytes.extend(chunk)
                        if len(content_bytes) >= self.max_bytes:
                            break

                    elapsed_ms = (time.perf_counter() - start_time) * 1000.0
                    content_str = content_bytes[: self.max_bytes].decode("utf-8", errors="ignore")
                    accessible = 200 <= status_code < 400

                    title = extract_title_from_html(content_str)
                    snippet = extract_visible_text_snippet(content_str)

                    domain_matches = False
                    if expected_domain:
                        final_host = (urlparse(final_url).hostname or "").lower().replace("www.", "")
                        norm_exp = expected_domain.lower().replace("www.", "")
                        domain_matches = norm_exp in final_host or final_host in norm_exp

                    biz_found = False
                    if business_name and business_name.strip():
                        search_target = f"{title or ''} {snippet}".lower()
                        biz_found = business_name.strip().lower() in search_target

                    return WebsiteFetchResult(
                        accessible=accessible,
                        status_code=status_code,
                        final_url=final_url,
                        domain_matches=domain_matches,
                        business_name_found=biz_found,
                        title=title,
                        html_content=content_str,
                        response_time_ms=round(elapsed_ms, 2),
                        headers=headers_dict,
                    )
        except httpx.TimeoutException:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return WebsiteFetchResult(accessible=False, response_time_ms=round(elapsed_ms, 2), error_message="Timeout")
        except httpx.TooManyRedirects:
            return WebsiteFetchResult(accessible=False, error_message="Too many redirects")
        except Exception as e:
            return WebsiteFetchResult(accessible=False, error_message=f"Connection error: {str(e)}")
