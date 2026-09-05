from typing import List, Optional
from app.core.exceptions import NotFoundError, ValidationError
from app.repositories.business import BusinessRepository
from app.repositories.lead import LeadRepository
from app.repositories.outreach import OutreachRepository
from app.schemas.api import OutreachCreateRequest, OutreachUpdateRequest
from app.schemas.common import utc_now
from app.schemas.enums import OutreachStatus
from app.schemas.outreach import Outreach


class OutreachService:
    def __init__(
        self,
        outreach_repo: Optional[OutreachRepository] = None,
        lead_repo: Optional[LeadRepository] = None,
        business_repo: Optional[BusinessRepository] = None,
    ):
        self.outreach_repo = outreach_repo or OutreachRepository()
        self.lead_repo = lead_repo or LeadRepository()
        self.business_repo = business_repo or BusinessRepository()

    async def create_outreach(self, req: OutreachCreateRequest) -> Outreach:
        lead_doc = await self.lead_repo.get_by_id(req.lead_id)
        if not lead_doc:
            raise NotFoundError(f"Lead with ID '{req.lead_id}' not found.")

        biz_doc = await self.business_repo.get_by_id(req.business_id)
        if not biz_doc:
            raise NotFoundError(f"Business with ID '{req.business_id}' not found.")

        # Default new outreach to DRAFT or READY if specified safely
        initial_status = req.status
        if initial_status not in [OutreachStatus.DRAFT, OutreachStatus.READY]:
            initial_status = OutreachStatus.DRAFT

        outreach_obj = Outreach(
            lead_id=self.outreach_repo.parse_object_id(req.lead_id),
            business_id=self.outreach_repo.parse_object_id(req.business_id),
            channel=req.channel,
            direction=req.direction,
            message_type=req.message_type,
            subject=req.subject,
            message=req.message,
            status=initial_status,
        )

        doc = outreach_obj.model_dump(by_alias=True, exclude={"id"})
        created_doc = await self.outreach_repo.create(doc)
        return Outreach(**created_doc)

    async def get_outreach(self, outreach_id: str) -> Outreach:
        doc = await self.outreach_repo.get_by_id(outreach_id)
        if not doc:
            raise NotFoundError(f"Outreach record with ID '{outreach_id}' not found.")
        return Outreach(**doc)

    async def list_outreach_for_lead(self, lead_id: str) -> List[Outreach]:
        await self.lead_repo.get_by_id(lead_id)
        items = await self.outreach_repo.list_by_lead_id(lead_id)
        return [Outreach(**d) for d in items]

    async def update_outreach(self, outreach_id: str, req: OutreachUpdateRequest) -> Outreach:
        existing = await self.outreach_repo.get_by_id(outreach_id)
        if not existing:
            raise NotFoundError(f"Outreach record with ID '{outreach_id}' not found.")

        update_data = req.model_dump(exclude_unset=True)
        if not update_data:
            return Outreach(**existing)

        if "status" in update_data and update_data["status"] is not None:
            new_status = update_data["status"]
            if new_status in [OutreachStatus.SENT, OutreachStatus.DELIVERED, OutreachStatus.FAILED]:
                status_str = new_status.value if hasattr(new_status, "value") else str(new_status)
                raise ValidationError(
                    f"Direct transition to status '{status_str}' is not permitted via standard update endpoint."
                )

        update_data["updated_at"] = utc_now()
        updated_doc = await self.outreach_repo.update_by_id(outreach_id, update_data)
        return Outreach(**updated_doc)
