from fastapi import APIRouter, Depends, status
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import List

from db.main import get_session
from controllers.messages_ctrl import MessageCtrl
from schemas.messages_schema import (
    MessageCreate,
    MessageRead
)

messages_router = APIRouter(
    prefix="/api/messages",
    tags=["Messages"]
)

messages_ctrl = MessageCtrl()

@messages_router.post("/", response_model=MessageRead, status_code=status.HTTP_201_CREATED)
async def send_message(
    message_data: MessageCreate, 
    session: AsyncSession = Depends(get_session)
):
    new_interaction = await messages_ctrl.create_message(message_data, session)
    return new_interaction


@messages_router.get("/conversation/{conversation_id}", response_model=List[MessageRead])
async def get_chat_history(
    conversation_id: int, 
    session: AsyncSession = Depends(get_session)
):
    history = await messages_ctrl.get_messages_for_conversation(conversation_id, session)
    return history

@messages_router.get("/{message_id}", response_model=MessageRead)
async def get_message(
    message_id: int, 
    session: AsyncSession = Depends(get_session)
):
    message = await messages_ctrl.get_message_by_id(message_id, session)
    return message