from typing import List, Optional
from app.core.exceptions import NotFoundError
from app.repositories.business import BusinessRepository
from app.repositories.conversation import ConversationRepository
from app.repositories.lead import LeadRepository
from app.schemas.api import ConversationCreateRequest, ConversationUpdateRequest
from app.schemas.common import utc_now
from app.schemas.conversation import Conversation


class ConversationService:
    def __init__(
        self,
        conversation_repo: Optional[ConversationRepository] = None,
        lead_repo: Optional[LeadRepository] = None,
        business_repo: Optional[BusinessRepository] = None,
    ):
        self.conversation_repo = conversation_repo or ConversationRepository()
        self.lead_repo = lead_repo or LeadRepository()
        self.business_repo = business_repo or BusinessRepository()

    async def create_conversation(self, req: ConversationCreateRequest) -> Conversation:
        lead_doc = await self.lead_repo.get_by_id(req.lead_id)
        if not lead_doc:
            raise NotFoundError(f"Lead with ID '{req.lead_id}' not found.")

        biz_doc = await self.business_repo.get_by_id(req.business_id)
        if not biz_doc:
            raise NotFoundError(f"Business with ID '{req.business_id}' not found.")

        conv_obj = Conversation(
            lead_id=self.conversation_repo.parse_object_id(req.lead_id),
            business_id=self.conversation_repo.parse_object_id(req.business_id),
            channel=req.channel,
            status=req.status,
            sentiment=req.sentiment,
            intent=req.intent,
            ai_summary=req.ai_summary,
            next_action=req.next_action,
            next_follow_up_at=req.next_follow_up_at,
        )

        doc = conv_obj.model_dump(by_alias=True, exclude={"id"})
        created_doc = await self.conversation_repo.create(doc)
        return Conversation(**created_doc)

    async def get_conversation(self, conversation_id: str) -> Conversation:
        doc = await self.conversation_repo.get_by_id(conversation_id)
        if not doc:
            raise NotFoundError(f"Conversation record with ID '{conversation_id}' not found.")
        return Conversation(**doc)

    async def get_conversation_for_lead(self, lead_id: str) -> List[Conversation]:
        await self.lead_repo.get_by_id(lead_id)
        items = await self.conversation_repo.find_by_lead_id(lead_id)
        return [Conversation(**d) for d in items]

    async def update_conversation(
        self, conversation_id: str, req: ConversationUpdateRequest
    ) -> Conversation:
        existing = await self.conversation_repo.get_by_id(conversation_id)
        if not existing:
            raise NotFoundError(f"Conversation record with ID '{conversation_id}' not found.")

        update_data = req.model_dump(exclude_unset=True)
        if not update_data:
            return Conversation(**existing)

        update_data["updated_at"] = utc_now()
        updated_doc = await self.conversation_repo.update_by_id(conversation_id, update_data)
        return Conversation(**updated_doc)
