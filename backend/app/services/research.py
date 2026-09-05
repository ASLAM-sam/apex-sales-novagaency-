from typing import List, Optional
from app.core.exceptions import NotFoundError
from app.repositories.business import BusinessRepository
from app.repositories.lead import LeadRepository
from app.repositories.research import ResearchRepository
from app.schemas.api import ResearchCreateRequest
from app.schemas.research import Research


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

    async def create_research(self, req: ResearchCreateRequest) -> Research:
        biz_doc = await self.business_repo.get_by_id(req.business_id)
        if not biz_doc:
            raise NotFoundError(f"Business with ID '{req.business_id}' not found.")

        lead_oid = None
        if req.lead_id:
            lead_doc = await self.lead_repo.get_by_id(req.lead_id)
            if not lead_doc:
                raise NotFoundError(f"Lead with ID '{req.lead_id}' not found.")
            lead_oid = self.research_repo.parse_object_id(req.lead_id)

        research_obj = Research(
            business_id=self.research_repo.parse_object_id(req.business_id),
            lead_id=lead_oid,
            business_summary=req.business_summary,
            products_services=req.products_services,
            target_audience=req.target_audience,
            location_summary=req.location_summary,
            online_presence=req.online_presence,
            social_presence=req.social_presence,
            competitive_context=req.competitive_context,
            business_signals=req.business_signals,
            research_sources=req.research_sources,
            research_confidence=req.research_confidence,
            research_version=req.research_version,
        )

        doc = research_obj.model_dump(by_alias=True, exclude={"id"})
        created_doc = await self.research_repo.create(doc)
        return Research(**created_doc)

    async def get_research(self, research_id: str) -> Research:
        doc = await self.research_repo.get_by_id(research_id)
        if not doc:
            raise NotFoundError(f"Research record with ID '{research_id}' not found.")
        return Research(**doc)

    async def get_research_by_business(self, business_id: str) -> List[Research]:
        await self.business_repo.get_by_id(business_id)
        items = await self.research_repo.get_by_business_id(business_id)
        return [Research(**d) for d in items]

    async def get_research_by_lead(self, lead_id: str) -> List[Research]:
        await self.lead_repo.get_by_id(lead_id)
        items = await self.research_repo.get_by_lead_id(lead_id)
        return [Research(**d) for d in items]
