from typing import Any, Dict, Optional, Set, Tuple
from app.discovery.models import NormalizedCandidate
from app.repositories.business import BusinessRepository


class CandidateDeduplicator:
    """
    Deterministic deduplication helper.
    Prevents duplicates within a single batch run and matches against existing MongoDB business records.
    """

    def __init__(self, business_repo: Optional[BusinessRepository] = None):
        self.business_repo = business_repo or BusinessRepository()
        self._seen_domains: Set[str] = set()
        self._seen_phones: Set[str] = set()
        self._seen_name_city: Set[Tuple[str, str]] = set()

    def reset_batch_state(self) -> None:
        self._seen_domains.clear()
        self._seen_phones.clear()
        self._seen_name_city.clear()

    def is_batch_duplicate(self, candidate: NormalizedCandidate) -> bool:
        """
        Checks whether the candidate is a duplicate within the current discovery batch.
        """
        if candidate.normalized_domain and candidate.normalized_domain in self._seen_domains:
            return True

        if candidate.normalized_phone and candidate.normalized_phone in self._seen_phones:
            return True

        city_key = (candidate.city or "").strip().lower()
        if candidate.normalized_name and city_key:
            name_city = (candidate.normalized_name, city_key)
            if name_city in self._seen_name_city:
                return True

        # Record candidate identities in batch seen sets
        if candidate.normalized_domain:
            self._seen_domains.add(candidate.normalized_domain)
        if candidate.normalized_phone:
            self._seen_phones.add(candidate.normalized_phone)
        if candidate.normalized_name and city_key:
            self._seen_name_city.add((candidate.normalized_name, city_key))

        return False

    async def find_existing_business(self, candidate: NormalizedCandidate) -> Optional[Dict[str, Any]]:
        """
        Checks MongoDB business collection to find an existing business matching the candidate.
        Priority:
        1. normalized_domain
        2. normalized_phone
        3. normalized_name + city/location
        """
        if candidate.normalized_domain:
            existing = await self.business_repo.get_by_domain(candidate.normalized_domain)
            if existing:
                return existing

        if candidate.normalized_phone:
            existing = await self.business_repo.get_by_normalized_phone(candidate.normalized_phone)
            if existing:
                return existing

        if candidate.normalized_name:
            existing = await self.business_repo.get_by_normalized_name(candidate.normalized_name)
            if existing:
                existing_city = (existing.get("city") or "").strip().lower()
                candidate_city = (candidate.city or "").strip().lower()
                if not candidate_city or not existing_city or candidate_city == existing_city:
                    return existing

        return None
