import logging
from typing import Optional
from app.repositories.business import BusinessRepository
from app.repositories.lead import LeadRepository
from app.repositories.research import ResearchRepository
from app.schemas.business import Business
from app.schemas.common import utc_now
from app.schemas.lead import Lead
from app.schemas.research import Research, ResearchSource
from app.verification.models import WebsiteFetchResult
from app.research.extractor import extract_deterministic_research

logger = logging.getLogger(__name__)


class ResearchService:
    def __init__(
        self,
        research_repo: Optional[ResearchRepository] = None,
        business_repo: Optional[BusinessRepository] = None,
        lead_repo: Optional[LeadRepository] = None,
    ):
        self.research_repo = research_repo or ResearchRepository()
        self.business_repo = business_repo or BusinessRepository()
        self.lead_repo = lead_repo or LeadRepository()

    async def perform_research(
        self,
        business: Business,
        lead: Optional[Lead] = None,
        fetch_result: Optional[WebsiteFetchResult] = None,
    ) -> Research:
        """Perform deterministic business research and upsert into research collection."""
        biz_id_str = str(business.id) if business.id else None
        lead_id_str = str(lead.id) if lead and lead.id else None

        extracted = extract_deterministic_research(
            business_name=business.name,
            category=business.category,
            city=business.city,
            html=fetch_result.html_content if fetch_result else None,
            title=fetch_result.title if fetch_result else None,
        )

        sources = []
        if fetch_result and fetch_result.final_url:
            sources.append(
                ResearchSource(
                    source_type="website",
                    source_url=fetch_result.final_url,
                    title=fetch_result.title or business.name,
                )
            )
        elif business.website:
            sources.append(
                ResearchSource(
                    source_type="business_record",
                    source_url=business.website,
                    title=business.name,
                )
            )
        else:
            sources.append(
                ResearchSource(
                    source_type="manual_record",
                    title=business.name,
                )
            )

        # Check existing research records for this business
        existing_list = []
        if biz_id_str:
            existing_list = await self.research_repo.get_by_business_id(biz_id_str)

        biz_oid = self.research_repo.parse_object_id(biz_id_str) if biz_id_str else None
        lead_oid = self.research_repo.parse_object_id(lead_id_str) if lead_id_str else None

        if existing_list:
            # Upsert / update latest existing research record
            target_doc = existing_list[0]
            target_id = str(target_doc["_id"])
            update_fields = {
                "lead_id": lead_oid,
                "business_summary": extracted["business_summary"],
                "products_services": extracted["products_services"],
                "location_summary": extracted["location_summary"],
                "online_presence": extracted["online_presence"],
                "business_signals": extracted["business_signals"],
                "research_sources": [s.model_dump() for s in sources],
                "research_confidence": extracted["research_confidence"],
                "updated_at": utc_now(),
            }
            await self.research_repo.update_by_id(target_id, update_fields)
            updated_doc = await self.research_repo.get_by_id(target_id)
            return Research(**updated_doc)
        else:
            # Create new research record
            research_obj = Research(
                business_id=biz_oid,
                lead_id=lead_oid,
                business_summary=extracted["business_summary"],
                products_services=extracted["products_services"],
                location_summary=extracted["location_summary"],
                online_presence=extracted["online_presence"],
                business_signals=extracted["business_signals"],
                research_sources=sources,
                research_confidence=extracted["research_confidence"],
                research_version="1.0",
            )
            doc = research_obj.model_dump(by_alias=True, exclude={"id"})
            created_doc = await self.research_repo.create(doc)
            return Research(**created_doc)
