import logging
import time
from typing import Dict, List, Optional
from app.discovery.deduplicator import CandidateDeduplicator
from app.discovery.exceptions import UnsupportedDiscoverySourceError
from app.discovery.interfaces import BaseDiscoverySource
from app.discovery.models import DiscoverySummaryData
from app.discovery.normalizer import CandidateNormalizer
from app.discovery.schemas import DiscoverySearchRequest, DiscoverySearchResponse
from app.discovery.sources.manual import ManualDiscoverySource
from app.repositories.business import BusinessRepository
from app.repositories.lead import LeadRepository
from app.schemas.agent_run import AgentRun
from app.schemas.api import BusinessCreateRequest, BusinessUpdateRequest, LeadCreateRequest
from app.schemas.business import SourceRecord
from app.schemas.enums import AgentRunStatus, AgentType, LeadSource, LeadStatus, PipelineStage
from app.schemas.lead import Contact
from app.services.agent_run import AgentRunService
from app.services.business import BusinessService
from app.services.lead import LeadService

logger = logging.getLogger(__name__)


def map_lead_source(source_str: str) -> LeadSource:
    s = source_str.upper()
    if s == "MANUAL":
        return LeadSource.MANUAL
    elif s in ("GOOGLE_MAPS", "GOOGLEMAPS", "MAPS"):
        return LeadSource.GOOGLE_MAPS
    elif s in ("DIRECTORY", "DIRECTORIES"):
        return LeadSource.DIRECTORY
    elif s in ("WEBSITE", "WEB"):
        return LeadSource.WEBSITE
    elif s == "IMPORT":
        return LeadSource.IMPORT
    return LeadSource.OTHER


class DiscoveryService:
    """
    Service orchestrator for lead discovery runs.
    Manages discovery sources, normalizes candidates, handles deduplication,
    creates/merges businesses and leads safely, and logs execution history.
    """

    def __init__(
        self,
        sources: Optional[Dict[str, BaseDiscoverySource]] = None,
        business_service: Optional[BusinessService] = None,
        lead_service: Optional[LeadService] = None,
        agent_run_service: Optional[AgentRunService] = None,
        business_repo: Optional[BusinessRepository] = None,
        lead_repo: Optional[LeadRepository] = None,
    ):
        manual_src = ManualDiscoverySource()
        self.sources: Dict[str, BaseDiscoverySource] = sources or {manual_src.source_name: manual_src}

        self.business_repo = business_repo or BusinessRepository()
        self.lead_repo = lead_repo or LeadRepository()

        self.business_service = business_service or BusinessService(self.business_repo)
        self.lead_service = lead_service or LeadService(self.lead_repo, self.business_repo)
        self.agent_run_service = agent_run_service or AgentRunService()
        self.deduplicator = CandidateDeduplicator(self.business_repo)

    async def discover(self, request: DiscoverySearchRequest) -> DiscoverySearchResponse:
        source_key = request.source.lower().strip()
        if source_key not in self.sources:
            raise UnsupportedDiscoverySourceError(f"Discovery source '{request.source}' is not supported.")

        source = self.sources[source_key]
        start_time = time.time()

        run_record: Optional[AgentRun] = None
        try:
            agent_run_doc = AgentRun(
                agent_type=AgentType.LEAD_DISCOVERY,
                run_type=source_key,
                status=AgentRunStatus.RUNNING,
                input_reference=f"query={request.query}, location={request.location}, max={request.max_results}",
            )
            run_record = await self.agent_run_service.create_run(agent_run_doc)
        except Exception as run_exc:
            logger.warning(f"Failed to record AgentRun start: {run_exc}")

        raw_candidates = await source.search(request)
        capped_candidates = raw_candidates[: request.max_results]

        requested_count = (
            len(request.manual_candidates)
            if source_key == "manual" and request.manual_candidates is not None
            else request.max_results
        )
        received_count = len(capped_candidates)

        valid_count = 0
        duplicate_count = 0
        new_businesses = 0
        existing_businesses = 0
        new_leads = 0
        invalid_candidates = 0

        created_business_ids: List[str] = []
        created_lead_ids: List[str] = []

        self.deduplicator.reset_batch_state()

        for raw_cand in capped_candidates:
            norm_cand = CandidateNormalizer.normalize_candidate(raw_cand)
            if not norm_cand:
                invalid_candidates += 1
                continue

            if self.deduplicator.is_batch_duplicate(norm_cand):
                duplicate_count += 1
                continue

            valid_count += 1

            existing_biz = await self.deduplicator.find_existing_business(norm_cand)

            if existing_biz:
                existing_businesses += 1
                biz_id = str(existing_biz["_id"])

                update_fields: Dict[str, str] = {}
                if not existing_biz.get("website") and norm_cand.website:
                    update_fields["website"] = norm_cand.website
                if not existing_biz.get("phone") and norm_cand.phone:
                    update_fields["phone"] = norm_cand.phone
                if not existing_biz.get("email") and norm_cand.email:
                    update_fields["email"] = norm_cand.email
                if not existing_biz.get("address") and norm_cand.address:
                    update_fields["address"] = norm_cand.address
                if not existing_biz.get("city") and norm_cand.city:
                    update_fields["city"] = norm_cand.city
                if not existing_biz.get("state") and norm_cand.state:
                    update_fields["state"] = norm_cand.state
                if not existing_biz.get("country") and norm_cand.country:
                    update_fields["country"] = norm_cand.country

                if update_fields:
                    try:
                        update_req = BusinessUpdateRequest(**update_fields)
                        await self.business_service.update_business(biz_id, update_req)
                    except Exception as update_exc:
                        logger.warning(f"Failed conservative update on existing business {biz_id}: {update_exc}")

                existing_leads = await self.lead_repo.find_by_business_id(biz_id)
                if not existing_leads:
                    try:
                        lead_req = LeadCreateRequest(
                            business_id=biz_id,
                            lead_source=map_lead_source(norm_cand.source),
                            lead_status=LeadStatus.NEW,
                            pipeline_stage=PipelineStage.NEW,
                            contact=Contact(email=norm_cand.email, phone=norm_cand.phone),
                        )
                        created_lead = await self.lead_service.create_lead(lead_req)
                        created_lead_ids.append(str(created_lead.id))
                        new_leads += 1
                    except Exception as lead_exc:
                        logger.warning(f"Failed to create lead for existing business {biz_id}: {lead_exc}")

            else:
                source_record = SourceRecord(
                    source_type=norm_cand.source,
                    source_url=norm_cand.source_url,
                    source_name=norm_cand.source,
                )
                biz_req = BusinessCreateRequest(
                    name=norm_cand.name,
                    website=norm_cand.website,
                    phone=norm_cand.phone,
                    email=norm_cand.email,
                    address=norm_cand.address,
                    city=norm_cand.city,
                    state=norm_cand.state,
                    country=norm_cand.country,
                    category=norm_cand.category,
                    description=norm_cand.description,
                    social_profiles=norm_cand.social_profiles,
                    source_records=[source_record],
                )

                try:
                    created_biz = await self.business_service.create_business(biz_req)
                    biz_id = str(created_biz.id)
                    created_business_ids.append(biz_id)
                    new_businesses += 1

                    lead_req = LeadCreateRequest(
                        business_id=biz_id,
                        lead_source=map_lead_source(norm_cand.source),
                        lead_status=LeadStatus.NEW,
                        pipeline_stage=PipelineStage.NEW,
                        contact=Contact(email=norm_cand.email, phone=norm_cand.phone),
                    )
                    created_lead = await self.lead_service.create_lead(lead_req)
                    created_lead_ids.append(str(created_lead.id))
                    new_leads += 1

                except Exception as create_exc:
                    logger.error(f"Failed to create new business or lead for {norm_cand.name}: {create_exc}")

        duration_ms = int((time.time() - start_time) * 1000)

        if run_record and run_record.id:
            try:
                run_id_str = str(run_record.id)
                await self.agent_run_service.run_repo.update_by_id(
                    run_id_str,
                    {
                        "status": AgentRunStatus.COMPLETED,
                        "duration_ms": duration_ms,
                        "output_reference": f"new_biz={new_businesses}, new_leads={new_leads}, duplicates={duplicate_count}",
                    },
                )
            except Exception as run_update_exc:
                logger.warning(f"Failed to update AgentRun status: {run_update_exc}")

        summary = DiscoverySummaryData(
            run_id=str(run_record.id) if run_record and run_record.id else None,
            source=source_key,
            requested=requested_count,
            received=received_count,
            valid=valid_count,
            duplicates=duplicate_count,
            new_businesses=new_businesses,
            existing_businesses=existing_businesses,
            new_leads=new_leads,
            invalid_candidates=invalid_candidates,
            created_business_ids=created_business_ids,
            created_lead_ids=created_lead_ids,
        )

        return DiscoverySearchResponse(data=summary)
        manual_src = ManualDiscoverySource()
        self.sources: Dict[str, BaseDiscoverySource] = sources or {manual_src.source_name: manual_src}

        self.business_repo = business_repo or BusinessRepository()
        self.lead_repo = lead_repo or LeadRepository()

        self.business_service = business_service or BusinessService(self.business_repo)
        self.lead_service = lead_service or LeadService(self.lead_repo, self.business_repo)
        self.agent_run_service = agent_run_service or AgentRunService()
        self.deduplicator = CandidateDeduplicator(self.business_repo)
