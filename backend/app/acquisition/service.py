import logging
import uuid
from typing import List, Optional
from app.acquisition.exceptions import AcquisitionError
from app.acquisition.registry import SourceRegistry, get_default_registry
from app.acquisition.schemas import (
    AcquisitionCandidate,
    AcquisitionImportRequest,
    AcquisitionImportResponse,
    AcquisitionLocation,
    AcquisitionSearchRequest,
    AcquisitionSearchResponse,
)
from app.discovery.deduplicator import CandidateDeduplicator
from app.discovery.models import DiscoveredCandidate, NormalizedCandidate
from app.discovery.normalizer import CandidateNormalizer
from app.discovery.service import map_lead_source
from app.repositories.business import BusinessRepository
from app.repositories.lead import LeadRepository
from app.schemas.api import BusinessCreateRequest, LeadCreateRequest
from app.schemas.enums import LeadStatus, PipelineStage
from app.schemas.lead import Contact
from app.services.business import BusinessService
from app.services.lead import LeadService
from app.schemas.business import SocialProfiles

logger = logging.getLogger(__name__)


class LeadAcquisitionService:
    """
    Lead Acquisition Service.
    Orchestrates provider-independent candidate business searches and explicit candidate imports.
    """

    def __init__(
        self,
        registry: Optional[SourceRegistry] = None,
        business_repo: Optional[BusinessRepository] = None,
        lead_repo: Optional[LeadRepository] = None,
        business_service: Optional[BusinessService] = None,
        lead_service: Optional[LeadService] = None,
    ) -> None:
        self.registry = registry or get_default_registry()
        self.business_repo = business_repo or BusinessRepository()
        self.lead_repo = lead_repo or LeadRepository()
        self.business_service = business_service or BusinessService(self.business_repo)
        self.lead_service = lead_service or LeadService(self.lead_repo, self.business_repo)
        self.deduplicator = CandidateDeduplicator(self.business_repo)
    async def search(self, request: AcquisitionSearchRequest) -> AcquisitionSearchResponse:
        source_impl = self.registry.get(request.source)
        discovered_raw: List[DiscoveredCandidate] = await source_impl.search(request)

        capped = discovered_raw[: request.limit]
        self.deduplicator.reset_batch_state()

        candidate_outputs: List[AcquisitionCandidate] = []

        for item in capped:
            norm: Optional[NormalizedCandidate] = CandidateNormalizer.normalize_candidate(item)
            if not norm:
                continue

            if self.deduplicator.is_batch_duplicate(norm):
                continue

            existing_biz = await self.deduplicator.find_existing_business(norm)
            already_exists = False
            existing_biz_id: Optional[str] = None
            existing_lead_id: Optional[str] = None
            qual_state: Optional[str] = None

            if existing_biz:
                already_exists = True
                existing_biz_id = str(existing_biz["_id"])
                existing_leads = await self.lead_repo.find_by_business_id(existing_biz_id)
                if existing_leads:
                    lead_doc = existing_leads[0]
                    existing_lead_id = str(lead_doc["_id"])
                    qual_state = (
                        lead_doc.get("qualification", {}).get("qualification_status")
                        or lead_doc.get("lead_status")
                    )

            candidate_id = item.source_id or str(uuid.uuid4())

            cand_out = AcquisitionCandidate(
                candidate_id=candidate_id,
                name=norm.name,
                website=norm.website,
                phone=norm.phone,
                email=norm.email,
                location=AcquisitionLocation(
                    address=norm.address,
                    city=norm.city,
                    state=norm.state,
                    country=norm.country,
                ),
                address=norm.address,
                city=norm.city,
                state=norm.state,
                country=norm.country,
                category=norm.category,
                description=norm.description,
                source=norm.source,
                already_exists=already_exists,
                existing_business_id=existing_biz_id,
                existing_lead_id=existing_lead_id,
                qualification_state=qual_state,
                raw_data=norm.raw_data,
            )
            candidate_outputs.append(cand_out)

        return AcquisitionSearchResponse(
            candidates=candidate_outputs,
            total=len(candidate_outputs),
            source=request.source,
        )
    async def import_candidates(self, request: AcquisitionImportRequest) -> AcquisitionImportResponse:
        self.deduplicator.reset_batch_state()

        imported_count = 0
        already_exists_count = 0
        duplicates_count = 0
        invalid_count = 0
        failed_count = 0

        business_ids: List[str] = []
        lead_ids: List[str] = []
        details: List[dict] = []

        for idx, item in enumerate(request.candidates):
            try:
                disc_cand = DiscoveredCandidate(
                    name=(item.name or "").strip(),
                    website=(item.website or "").strip() or None,
                    phone=(item.phone or "").strip() or None,
                    email=(item.email or "").strip() or None,
                    address=(item.address or "").strip() or None,
                    city=(item.city or "").strip() or None,
                    state=(item.state or "").strip() or None,
                    country=(item.country or "").strip() or None,
                    category=(item.category or "").strip() or None,
                    description=(item.description or "").strip() or None,
                    source=(item.source_name or "manual").strip(),
                    source_id=item.source_id or f"import-{idx+1}",
                    social_profiles=item.social_profiles or {},
                    raw_data=item.raw_data or {},
                )

                norm: Optional[NormalizedCandidate] = CandidateNormalizer.normalize_candidate(disc_cand)
                if not norm:
                    invalid_count += 1
                    details.append({"index": idx, "status": "invalid", "reason": "Missing minimum business fields"})
                    continue

                if self.deduplicator.is_batch_duplicate(norm):
                    duplicates_count += 1
                    details.append({"index": idx, "name": norm.name, "status": "duplicate_in_batch"})
                    continue

                existing_biz = await self.deduplicator.find_existing_business(norm)
                if existing_biz:
                    biz_id = str(existing_biz["_id"])
                else:
                    create_req = BusinessCreateRequest(
                        name=norm.name,
                        website=norm.website,
                        phone=norm.phone,
                        email=norm.email,
                        address=norm.address,
                        city=norm.city,
                        state=norm.state,
                        country=norm.country,
                        category=norm.category,
                        description=norm.description,
                        social_profiles=SocialProfiles(**norm.social_profiles) if norm.social_profiles else SocialProfiles(),
                    )
                    created_biz = await self.business_service.create_business(create_req)
                    biz_id = str(created_biz.id)

                if biz_id not in business_ids:
                    business_ids.append(biz_id)

                existing_leads = await self.lead_repo.find_by_business_id(biz_id)
                if existing_leads:
                    active_lead = existing_leads[0]
                    existing_lead_id = str(active_lead["_id"])
                    lead_status_str = active_lead.get("lead_status", "")

                    already_exists_count += 1
                    if existing_lead_id not in lead_ids:
                        lead_ids.append(existing_lead_id)

                    details.append({
                        "index": idx,
                        "name": norm.name,
                        "status": "already_exists",
                        "business_id": biz_id,
                        "lead_id": existing_lead_id,
                        "lead_status": lead_status_str,
                    })
                    continue

                lead_src = map_lead_source(norm.source)
                contact_obj = Contact(
                    name=norm.name,
                    email=norm.email,
                    phone=norm.phone,
                )
                lead_create_req = LeadCreateRequest(
                    business_id=biz_id,
                    contact=contact_obj,
                    lead_source=lead_src,
                    lead_status=LeadStatus.NEW,
                    pipeline_stage=PipelineStage.DISCOVERED,
                )
                created_lead = await self.lead_service.create_lead(lead_create_req)
                new_lead_id = str(created_lead.id)

                imported_count += 1
                lead_ids.append(new_lead_id)
                details.append({
                    "index": idx,
                    "name": norm.name,
                    "status": "imported",
                    "business_id": biz_id,
                    "lead_id": new_lead_id,
                })

            except Exception as exc:
                logger.error(f"Error importing candidate at index {idx}: {exc}")
                failed_count += 1
                details.append({"index": idx, "status": "failed", "error": str(exc)})

        return AcquisitionImportResponse(
            imported=imported_count,
            already_exists=already_exists_count,
            duplicates=duplicates_count,
            invalid=invalid_count,
            failed=failed_count,
            business_ids=business_ids,
            lead_ids=lead_ids,
            details=details,
        )
