import re
from typing import Optional, Tuple
from app.discovery.models import DiscoveredCandidate, NormalizedCandidate


class CandidateNormalizer:
    """
    Deterministic normalizer for business candidates.
    Performs cheap, predictable domain, phone, email, and name normalization without LLMs.
    """

    @staticmethod
    def normalize_name(name: Optional[str]) -> Tuple[str, str]:
        if not name:
            return "", ""
        clean_name = re.sub(r"\s+", " ", name.strip())
        normalized_name = clean_name.lower()
        return clean_name, normalized_name

    @staticmethod
    def normalize_domain(url_or_domain: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
        if not url_or_domain:
            return None, None

        val = url_or_domain.strip().lower()
        if not val:
            return None, None

        # Determine scheme
        scheme = "https://" if val.startswith("https://") else "http://" if val.startswith("http://") else ""

        # Extract domain part
        domain_part = re.sub(r"^https?://", "", val)
        domain_part = domain_part.split("/")[0].split("?")[0].split("#")[0].strip()

        # Remove leading www.
        if domain_part.startswith("www."):
            domain_part = domain_part[4:]

        if not domain_part or "." not in domain_part:
            return None, None

        normalized_domain = domain_part
        # Construct clean website URL
        clean_website = f"{scheme if scheme else 'https://'}{domain_part}"

        return clean_website, normalized_domain

    @staticmethod
    def normalize_phone(phone: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
        if not phone:
            return None, None

        raw = phone.strip()
        if not raw:
            return None, None

        # Retain leading '+' if present
        has_plus = raw.startswith("+")
        digits = re.sub(r"\D", "", raw)

        if not digits or len(digits) < 5:
            return raw, None

        normalized_phone = f"+{digits}" if has_plus else digits
        return raw, normalized_phone

    @staticmethod
    def normalize_email(email: Optional[str]) -> Optional[str]:
        if not email:
            return None

        val = email.strip().lower()
        # Basic RFC-compliant regex check
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        if re.match(pattern, val):
            return val
        return None

    @staticmethod
    def normalize_url(url: Optional[str]) -> Optional[str]:
        if not url:
            return None
        val = url.strip()
        if val.endswith("/") and len(val) > 8:
            val = val.rstrip("/")
        return val if val else None

    @classmethod
    def normalize_candidate(cls, candidate: DiscoveredCandidate) -> Optional[NormalizedCandidate]:
        raw_name, norm_name = cls.normalize_name(candidate.name)
        website, norm_domain = cls.normalize_domain(candidate.website or candidate.domain)
        phone, norm_phone = cls.normalize_phone(candidate.phone)
        email = cls.normalize_email(candidate.email)
        url = cls.normalize_url(candidate.source_url)

        # Rejection rule: Candidate must have a non-empty name OR a valid normalized domain/phone
        if not raw_name and not norm_domain and not norm_phone:
            return None

        display_name = raw_name or norm_domain or "Unknown Business"

        return NormalizedCandidate(
            name=display_name,
            normalized_name=norm_name or display_name.lower(),
            website=website,
            normalized_domain=norm_domain,
            phone=phone,
            normalized_phone=norm_phone,
            email=email,
            address=candidate.address.strip() if candidate.address else None,
            city=candidate.city.strip() if candidate.city else None,
            state=candidate.state.strip() if candidate.state else None,
            country=candidate.country.strip() if candidate.country else None,
            category=candidate.category.strip() if candidate.category else None,
            description=candidate.description.strip() if candidate.description else None,
            social_profiles=candidate.social_profiles,
            source=candidate.source,
            source_id=candidate.source_id,
            source_url=url,
            raw_data=candidate.raw_data,
            discovered_at=candidate.discovered_at,
        )
