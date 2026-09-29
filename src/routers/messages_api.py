from fastapi import APIRouter, Depends, status
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import List
from urllib.parse import urlparse, unquote

from db.main import get_session
from controllers.messages_ctrl import MessageCtrl
from schemas.messages_schema import (
    MessageCreate,
    MessageRead
)
from utils.auth.dependencies import get_current_user, RoleChecker
from utils.errors import NoPermission
from utils.s3_storage import storage
from models import User

messages_router = APIRouter(
    prefix="/api/messages",
    tags=["Messages"]
)

user_allowed = RoleChecker(["user"])
messages_ctrl = MessageCtrl()


@messages_router.post("/", response_model=MessageRead, status_code=status.HTTP_201_CREATED)
async def send_message(
    message_data: MessageCreate, 
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(user_allowed)):
    """Send a message. User must own the conversation."""
    
    new_interaction = await messages_ctrl.create_message(message_data, session)
    return new_interaction


@messages_router.get("/conversation/{conversation_id}", response_model=List[MessageRead])
async def get_chat_history(
    conversation_id: int, 
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(user_allowed)):
    """Get chat history for a conversation. Superadmin can access any conversation."""

    from controllers.conversations_ctrl import ConversationCtrl
    conv_ctrl = ConversationCtrl()
    conversation = await conv_ctrl.get_conversation(conversation_id, session)

    # Ownership check: only owner or superadmin can see messages
    if current_user.role != "superadmin" and conversation.user_id != current_user.id:
        raise NoPermission()

    history = await messages_ctrl.get_messages_for_conversation(conversation_id, session)

    def refresh_url(url: str) -> str:
        """Re-generate a fresh presigned URL from a stored one to avoid expiry."""
        try:
            parsed = urlparse(url)
            parts = parsed.path.lstrip("/").split("/", 1)
            if len(parts) == 2:
                return storage.generate_url(unquote(parts[1]))
        except Exception:
            pass
        return url

    for msg in history:
        if msg.image_urls:
            msg.image_urls = [refresh_url(u) for u in msg.image_urls]

    return history


@messages_router.get("/{message_id}", response_model=MessageRead)
async def get_message(
    message_id: int, 
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
    _: bool = Depends(user_allowed)):
    """Get a specific message by ID."""

    message = await messages_ctrl.get_message_by_id(message_id, session)
    return message