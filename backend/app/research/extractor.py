import re
from typing import Dict, List, Optional


def extract_meta_description(html: str) -> Optional[str]:
    """Extract <meta name="description"> or og:description from raw HTML."""
    if not html:
        return None

    # Check og:description
    match_og = re.search(
        r'<meta\s+[^>]*property=["\']og:description["\']\s+[^>]*content=["\'](.*?)["\']',
        html,
        re.IGNORECASE | re.DOTALL,
    )
    if match_og:
        return re.sub(r"\s+", " ", match_og.group(1).strip())[:500]

    # Check standard meta description
    match_desc = re.search(
        r'<meta\s+[^>]*name=["\']description["\']\s+[^>]*content=["\'](.*?)["\']',
        html,
        re.IGNORECASE | re.DOTALL,
    )
    if match_desc:
        return re.sub(r"\s+", " ", match_desc.group(1).strip())[:500]

    return None


def extract_headings(html: str, max_headings: int = 10) -> List[str]:
    """Extract h1 and h2 headings from raw HTML up to max_headings."""
    if not html:
        return []

    matches = re.findall(r"<h[12][^>]*>(.*?)</h[12]>", html, re.IGNORECASE | re.DOTALL)
    clean_headings = []
    for raw in matches:
        # Strip internal tags
        clean = re.sub(r"<[^>]+>", "", raw)
        clean = re.sub(r"\s+", " ", clean).strip()
        if clean and len(clean) > 3 and clean not in clean_headings:
            clean_headings.append(clean[:150])
            if len(clean_headings) >= max_headings:
                break
    return clean_headings


def detect_product_services(html: str, text_snippet: str, headings: List[str]) -> List[str]:
    """Detect potential products or services from website headings and text."""
    services = []
    keywords = [
        "service", "product", "offering", "solution", "development",
        "design", "marketing", "consulting", "repair", "maintenance",
        "installation", "agency", "store", "shop", "care", "dental"
    ]

    for heading in headings:
        heading_lower = heading.lower()
        if any(kw in heading_lower for kw in keywords):
            services.append(heading)

    if not services and text_snippet:
        words = text_snippet.split()
        for i, word in enumerate(words):
            if word.lower().strip(".,") in keywords and i < len(words) - 3:
                snippet = " ".join(words[max(0, i - 1) : min(len(words), i + 4)])
                services.append(snippet)
                if len(services) >= 3:
                    break

    return services[:5]


def extract_deterministic_research(
    business_name: str,
    category: Optional[str] = None,
    city: Optional[str] = None,
    html: Optional[str] = None,
    title: Optional[str] = None,
) -> Dict:
    """Extract structured research data deterministically from HTML and business fields."""
    meta_desc = extract_meta_description(html or "")
    headings = extract_headings(html or "")

    summary_parts = []
    if title:
        summary_parts.append(f"Title: {title}")
    if meta_desc:
        summary_parts.append(f"Description: {meta_desc}")
    elif headings:
        summary_parts.append(f"Primary Focus: {', '.join(headings[:3])}")
    else:
        summary_parts.append(f"{business_name} operating in {category or 'unspecified industry'}.")

    business_summary = " | ".join(summary_parts)[:1000]

    text_snippet = ""
    if html:
        clean = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", html, flags=re.IGNORECASE | re.DOTALL)
        clean = re.sub(r"<[^>]+>", " ", clean)
        text_snippet = re.sub(r"\s+", " ", clean).strip()[:1000]

    detected_services = detect_product_services(html or "", text_snippet, headings)
    if not detected_services and category:
        detected_services = [category]

    location_summary = city if city else "Location unspecified"

    signals = []
    if html:
        signals.append("Active website presence detected")
    if meta_desc:
        signals.append("Search meta description present")
    if headings:
        signals.append(f"Structured content with {len(headings)} main headings")

    return {
        "business_summary": business_summary,
        "products_services": detected_services,
        "location_summary": location_summary,
        "online_presence": f"Website title: '{title}'" if title else ("Website present" if html else "No website"),
        "business_signals": signals,
        "research_confidence": 0.85 if (html and meta_desc) else (0.70 if html else 0.40),
    }
