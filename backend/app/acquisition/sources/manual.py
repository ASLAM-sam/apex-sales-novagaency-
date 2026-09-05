from typing import List
from app.acquisition.interfaces import BaseLeadSource
from app.acquisition.schemas import AcquisitionSearchRequest
from app.discovery.models import DiscoveredCandidate
from app.schemas.business import SocialProfiles


class ManualLeadSource(BaseLeadSource):
    """
    Manual lead source implementation.
    Allows passing candidate business records directly without external APIs.
    """

    @property
    def source_name(self) -> str:
        return "manual"

    async def search(self, request: AcquisitionSearchRequest) -> List[DiscoveredCandidate]:
        if not request.manual_candidates:
            return []

        results: List[DiscoveredCandidate] = []
        for idx, item in enumerate(request.manual_candidates):
            name = (item.name or "").strip()
            website = (item.website or "").strip()
            phone = (item.phone or "").strip()
            email = (item.email or "").strip()
            city = (item.city or "").strip()
            state = (item.state or "").strip()
            country = (item.country or "").strip()
            category = (item.category or "").strip()

            # Filter checks
            if request.website_required and not website:
                continue

            if request.category and category and request.category.lower() not in category.lower():
                continue

            if request.city and city and request.city.lower() not in city.lower():
                continue

            if request.state and state and request.state.lower() not in state.lower():
                continue

            if request.country and country and request.country.lower() not in country.lower():
                continue

            if request.query:
                q = request.query.lower()
                matches_q = (
                    q in name.lower()
                    or q in website.lower()
                    or q in category.lower()
                    or q in (item.description or "").lower()
                )
                if not matches_q:
                    continue

            cand = DiscoveredCandidate(
                name=name or "Manual Candidate",
                website=website if website else None,
                phone=phone if phone else None,
                email=email if email else None,
                address=item.address.strip() if item.address else None,
                city=city if city else None,
                state=state if state else None,
                country=country if country else None,
                category=category if category else None,
                description=item.description.strip() if item.description else None,
                social_profiles=item.social_profiles or {},
                source=self.source_name,
                source_id=item.source_id or f"manual-{idx+1}",
                raw_data=item.raw_data or {},
            )
            results.append(cand)

        return results
