from fastapi import APIRouter, Depends, status
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import List, Dict

from db.main import get_session
from controllers.conversations_ctrl import ConversationCtrl
from schemas.conversations_schema import (
    ConversationCreate,
    ConversationUpdate,
    ConversationRead
)
from utils.auth.dependencies import AccessTokenBearer
from utils.auth.dependencies import RoleChecker, get_current_user
from utils.errors import ConversationNotFound, NoPermission
from models import User


conv_router = APIRouter(
     prefix="/api/conversations",
     tags=["Conversations"]
)

user_allowed = RoleChecker(["user"])
admin_allowed = RoleChecker(["admin"])
superadmin_allowed = RoleChecker(["superadmin"])

conv_ctrl = ConversationCtrl()
access_token_bearer = AccessTokenBearer() # protect endpoints


def ensure_conversation_owner_or_superadmin(conversation, current_user: User) -> None:
    if current_user.role == "superadmin":
        return

    if conversation.user_id != current_user.id:
        raise NoPermission()


@conv_router.get("/", response_model=List[ConversationRead])
async def get_all_conversations(
    session: AsyncSession = Depends(get_session),
    token: str = Depends(access_token_bearer),
    _: bool = Depends(superadmin_allowed)): # to protect endpoint

    conversations = await conv_ctrl.get_all_conversations(session)
    return conversations

@conv_router.get("/me", response_model=List[ConversationRead])
async def get_my_conversations(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(user_allowed)):

    conversations = await conv_ctrl.get_user_conversations(current_user.id, session)
    return conversations


@conv_router.get("/{conversation_id}", response_model=ConversationRead)
async def get_conversation(
    conversation_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(user_allowed)):
    """Get a conversation by ID. Ownership-checked."""

    conversation = await conv_ctrl.get_conversation(conversation_id, session)
    ensure_conversation_owner_or_superadmin(conversation, current_user)
    return conversation

@conv_router.post("/", response_model=ConversationRead, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    conversation_data: ConversationCreate, 
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(user_allowed)):
    """Create a new conversation. user_id is taken from the auth token automatically."""

    # Override user_id from token — client cannot spoof another user's ID
    conversation_data.user_id = current_user.id
    new_conv = await conv_ctrl.create_conversation(conversation_data, session)
    return new_conv

@conv_router.put("/{conversation_id}", response_model=ConversationRead)
async def update_conversation(
    conversation_id: int,
    conversation_data: ConversationUpdate,
    session: AsyncSession = Depends(get_session),
    token: str = Depends(access_token_bearer),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(user_allowed)):

    conversation = await conv_ctrl.get_conversation(conversation_id, session)
    ensure_conversation_owner_or_superadmin(conversation, current_user)

    # Pass the fetched object directly — no second DB round-trip
    updated_conv = await conv_ctrl.update_conversation(conversation, conversation_data, session)
    return updated_conv


@conv_router.delete("/{conversation_id}", response_model=Dict[str, str], status_code=status.HTTP_200_OK)
async def delete_conversation(
    conversation_id: int,
    session: AsyncSession = Depends(get_session),
    token: str = Depends(access_token_bearer),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(user_allowed)):

    conversation = await conv_ctrl.get_conversation(conversation_id, session)
    ensure_conversation_owner_or_superadmin(conversation, current_user)

    # Pass the fetched object directly — no second DB round-trip
    result = await conv_ctrl.delete_conversation(conversation, session)
    return result
