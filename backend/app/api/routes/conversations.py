from typing import List
from fastapi import APIRouter, Depends, status
from app.schemas.api import ConversationCreateRequest, ConversationUpdateRequest, SingleResponseEnvelope
from app.schemas.conversation import Conversation
from app.services.conversation import ConversationService

router = APIRouter(tags=["Conversations"])


def get_conversation_service() -> ConversationService:
    return ConversationService()


@router.post("/conversations", response_model=SingleResponseEnvelope[Conversation], status_code=status.HTTP_201_CREATED)
async def create_conversation(
    req: ConversationCreateRequest,
    service: ConversationService = Depends(get_conversation_service),
):
    conv = await service.create_conversation(req)
    return SingleResponseEnvelope(data=conv)


@router.get("/conversations/{conversation_id}", response_model=SingleResponseEnvelope[Conversation])
async def get_conversation(
    conversation_id: str,
    service: ConversationService = Depends(get_conversation_service),
):
    conv = await service.get_conversation(conversation_id)
    return SingleResponseEnvelope(data=conv)


@router.get("/leads/{lead_id}/conversation", response_model=SingleResponseEnvelope[List[Conversation]])
async def get_conversation_for_lead(
    lead_id: str,
    service: ConversationService = Depends(get_conversation_service),
):
    items = await service.get_conversation_for_lead(lead_id)
    return SingleResponseEnvelope(data=items)


@router.patch("/conversations/{conversation_id}", response_model=SingleResponseEnvelope[Conversation])
async def update_conversation(
    conversation_id: str,
    req: ConversationUpdateRequest,
    service: ConversationService = Depends(get_conversation_service),
):
    conv = await service.update_conversation(conversation_id, req)
    return SingleResponseEnvelope(data=conv)
