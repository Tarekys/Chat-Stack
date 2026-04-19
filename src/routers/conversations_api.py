from fastapi import APIRouter, Depends, status
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import List

from db.main import get_session
from controllers.conversations_ctrl import ConversationCtrl
from schemas.conversations_schema import (
    ConversationCreate,
    ConversationUpdate,
    ConversationRead
)
from schemas.users_schema import UserResponse
from utils.dependencies import AccessTokenBearer

conv_router = APIRouter(
     prefix="/api/conversations",
     tags=["Conversations"]
)

conv_ctrl = ConversationCtrl()
access_token_bearer = AccessTokenBearer() # protect endpoints

@conv_router.get("/", response_model=List[ConversationRead])
async def get_all_conversations(
    session: AsyncSession = Depends(get_session),
    token: str = Depends(access_token_bearer)
):
    print(token)
    conversations = await conv_ctrl.get_all_conversations(session)
    return conversations


@conv_router.get("/{conversation_id}", response_model=ConversationRead)
async def get_conversation(
    conversation_id: int,
    session: AsyncSession = Depends(get_session),
    token: str = Depends(access_token_bearer)
):

    conversation = await conv_ctrl.get_conversation(conversation_id, session)
    return conversation

@conv_router.post("/", response_model=ConversationRead, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    conversation_data: ConversationCreate, 
    session: AsyncSession = Depends(get_session),
    token: str = Depends(access_token_bearer)
):
    
    new_conv = await conv_ctrl.create_conversation(conversation_data, session)
    return new_conv

@conv_router.put("/{conversation_id}", response_model=ConversationRead)
async def update_conversation(
    conversation_id: int, 
    conversation_data: ConversationUpdate, 
    session: AsyncSession = Depends(get_session),
    token: str = Depends(access_token_bearer)
):
    updated_conv = await conv_ctrl.update_conversation(conversation_id, conversation_data, session)
    return updated_conv


@conv_router.delete("/{conversation_id}", response_model=UserResponse)
async def delete_conversation(
    conversation_id: int, 
    session: AsyncSession = Depends(get_session),
    token: str = Depends(access_token_bearer)
):
    
    result = await conv_ctrl.delete_conversation(conversation_id, session)
    return result