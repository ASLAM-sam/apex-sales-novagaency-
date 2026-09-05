import logging
from typing import List
from app.discovery.interfaces import BaseDiscoverySource
from app.discovery.models import DiscoveredCandidate
from app.discovery.schemas import DiscoverySearchRequest

logger = logging.getLogger(__name__)


class ManualDiscoverySource(BaseDiscoverySource):
    """
    Discovery source implementation for manually supplied structured candidates.
    Used for development testing, deterministic CSV/list inputs, and zero-cost operation.
    """

    @property
    def source_name(self) -> str:
        return "manual"

    async def search(self, request: DiscoverySearchRequest) -> List[DiscoveredCandidate]:
        candidates: List[DiscoveredCandidate] = []
        raw_items = request.manual_candidates or []

        for item in raw_items:
            if not isinstance(item, dict):
                logger.warning("Skipping non-dict candidate item in manual discovery source.")
                continue

            name = item.get("name") or item.get("business_name") or ""
            if not isinstance(name, str):
                name = str(name)

            social = item.get("social_profiles")
            social_dict = social if isinstance(social, dict) else {}

            candidate = DiscoveredCandidate(
                name=name.strip(),
                website=item.get("website") or item.get("url") or item.get("domain"),
                domain=item.get("domain"),
                phone=item.get("phone") or item.get("telephone") or item.get("mobile"),
                email=item.get("email"),
                address=item.get("address") or item.get("street_address"),
                city=item.get("city") or request.location,
                state=item.get("state"),
                country=item.get("country") or request.country,
                category=item.get("category") or item.get("industry") or request.category,
                description=item.get("description"),
                social_profiles=social_dict,
                source="manual",
                source_id=item.get("source_id"),
                source_url=item.get("source_url"),
                raw_data=item,
            )
            candidates.append(candidate)

        return candidates
