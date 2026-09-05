from typing import Any, Dict, List, Optional, Tuple
from app.core.exceptions import NotFoundError
from app.repositories.business import BusinessRepository
from app.repositories.lead import LeadRepository
from app.schemas.api import LeadCreateRequest, LeadUpdateRequest, PaginationMetadata
from app.schemas.common import utc_now
from app.schemas.lead import Contact, Lead, Qualification


class LeadService:
    def __init__(
        self,
        lead_repo: Optional[LeadRepository] = None,
        business_repo: Optional[BusinessRepository] = None,
    ):
        self.lead_repo = lead_repo or LeadRepository()
        self.business_repo = business_repo or BusinessRepository()

    async def create_lead(self, req: LeadCreateRequest) -> Lead:
        # Check associated business exists
        biz_doc = await self.business_repo.get_by_id(req.business_id)
        if not biz_doc:
            raise NotFoundError(f"Associated business with ID '{req.business_id}' not found.")

        lead_obj = Lead(
            business_id=self.lead_repo.parse_object_id(req.business_id),
            contact=req.contact or Contact(),
            lead_source=req.lead_source,
            source_reference=req.source_reference,
            lead_status=req.lead_status,
            pipeline_stage=req.pipeline_stage,
            qualification=req.qualification or Qualification(),
            score=req.score,
            service_opportunity=req.service_opportunity,
            evidence=req.evidence,
            next_follow_up_at=req.next_follow_up_at,
            assigned_to=req.assigned_to,
        )

        doc = lead_obj.model_dump(by_alias=True, exclude={"id"})
        created_doc = await self.lead_repo.create(doc)
        return Lead(**created_doc)

    async def get_lead(self, lead_id: str) -> Lead:
        doc = await self.lead_repo.get_by_id(lead_id)
        if not doc:
            raise NotFoundError(f"Lead with ID '{lead_id}' not found.")
        return Lead(**doc)

    async def list_leads(
        self,
        page: int = 1,
        page_size: int = 25,
        lead_status: Optional[str] = None,
        pipeline_stage: Optional[str] = None,
        lead_source: Optional[str] = None,
        business_id: Optional[str] = None,
        min_score: Optional[float] = None,
        max_score: Optional[float] = None,
    ) -> Tuple[List[Lead], PaginationMetadata]:
        page = max(1, page)
        page_size = min(max(1, page_size), 100)
        skip = (page - 1) * page_size

        query: Dict[str, Any] = {}
        if lead_status:
            query["lead_status"] = lead_status
        if pipeline_stage:
            query["pipeline_stage"] = pipeline_stage
        if lead_source:
            query["lead_source"] = lead_source
        if business_id:
            query["business_id"] = self.lead_repo.parse_object_id(business_id)

        if min_score is not None or max_score is not None:
            score_q = {}
            if min_score is not None:
                score_q["$gte"] = min_score
            if max_score is not None:
                score_q["$lte"] = max_score
            query["qualification.qualification_score"] = score_q

        items_docs, total = await self.lead_repo.list_leads(query, skip, page_size)
        pages = (total + page_size - 1) // page_size if total > 0 else 1

        leads = [Lead(**d) for d in items_docs]
        meta = PaginationMetadata(page=page, page_size=page_size, total=total, pages=pages)
        return leads, meta

    async def update_lead(self, lead_id: str, req: LeadUpdateRequest) -> Lead:
        existing = await self.lead_repo.get_by_id(lead_id)
        if not existing:
            raise NotFoundError(f"Lead with ID '{lead_id}' not found.")

        update_data = req.model_dump(exclude_unset=True)
        if not update_data:
            return Lead(**existing)

        update_data["updated_at"] = utc_now()
        updated_doc = await self.lead_repo.update_by_id(lead_id, update_data)
        return Lead(**updated_doc)
