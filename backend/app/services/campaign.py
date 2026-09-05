from typing import Any, Dict, List, Optional, Tuple
from app.core.exceptions import NotFoundError
from app.repositories.campaign import CampaignRepository
from app.schemas.api import CampaignCreateRequest, CampaignUpdateRequest, PaginationMetadata
from app.schemas.campaign import Campaign
from app.schemas.common import utc_now


class CampaignService:
    def __init__(self, campaign_repo: Optional[CampaignRepository] = None):
        self.campaign_repo = campaign_repo or CampaignRepository()

    async def create_campaign(self, req: CampaignCreateRequest) -> Campaign:
        campaign_obj = Campaign(
            name=req.name,
            description=req.description,
            status=req.status,
            target_service=req.target_service,
            target_industry=req.target_industry,
            lead_filters=req.lead_filters,
        )

        doc = campaign_obj.model_dump(by_alias=True, exclude={"id"})
        created_doc = await self.campaign_repo.create(doc)
        return Campaign(**created_doc)

    async def get_campaign(self, campaign_id: str) -> Campaign:
        doc = await self.campaign_repo.get_by_id(campaign_id)
        if not doc:
            raise NotFoundError(f"Campaign with ID '{campaign_id}' not found.")
        return Campaign(**doc)

    async def list_campaigns(
        self,
        page: int = 1,
        page_size: int = 25,
        status: Optional[str] = None,
    ) -> Tuple[List[Campaign], PaginationMetadata]:
        page = max(1, page)
        page_size = min(max(1, page_size), 100)
        skip = (page - 1) * page_size

        query: Dict[str, Any] = {}
        if status:
            query["status"] = status

        items_docs, total = await self.campaign_repo.list_campaigns(query, skip, page_size)
        pages = (total + page_size - 1) // page_size if total > 0 else 1

        campaigns = [Campaign(**d) for d in items_docs]
        meta = PaginationMetadata(page=page, page_size=page_size, total=total, pages=pages)
        return campaigns, meta

    async def update_campaign(self, campaign_id: str, req: CampaignUpdateRequest) -> Campaign:
        existing = await self.campaign_repo.get_by_id(campaign_id)
        if not existing:
            raise NotFoundError(f"Campaign with ID '{campaign_id}' not found.")

        update_data = req.model_dump(exclude_unset=True)
        if not update_data:
            return Campaign(**existing)

        update_data["updated_at"] = utc_now()
        updated_doc = await self.campaign_repo.update_by_id(campaign_id, update_data)
        return Campaign(**updated_doc)
