from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select, desc
import uuid

from models.conversations import Conversation
from schemas.conversations_schema import (
    ConversationCreate,
    ConversationUpdate
)
from utils.errors import ConversationNotFound

class ConversationCtrl:
    async def get_all_conversations(self, session: AsyncSession):
        
        stat = select(Conversation).where(Conversation.is_deleted == False).order_by(desc(Conversation.created_at))
        result = await session.exec(stat)
        return result.all()

    async def get_user_conversations(self, user_id: uuid.UUID, session: AsyncSession):
        
        stat = (
            select(Conversation)
            .where(
                Conversation.user_id == user_id,
                Conversation.is_deleted == False
            )
            .order_by(desc(Conversation.created_at))
        )
        result = await session.exec(stat)
        return result.all()

    async def get_conversation(self, conversation_id: int, session: AsyncSession):
        
        stat = select(Conversation).where(Conversation.id == conversation_id, Conversation.is_deleted == False)
        result = await session.exec(stat)
        conv = result.first()

        if not conv:
            raise ConversationNotFound()
        return conv

    async def create_conversation(self, conversation_data: ConversationCreate, session: AsyncSession):
        
        conv_dict = conversation_data.model_dump()
        new_conv = Conversation(**conv_dict)

        session.add(new_conv)
        await session.commit()
        await session.refresh(new_conv)
        return new_conv

    async def update_conversation(self, conversation: Conversation, conversation_data: ConversationUpdate, session: AsyncSession):
        """
        Accept the already-fetched Conversation object to avoid a second DB round-trip.
        The router is responsible for fetching & ownership-checking before calling this.
        """
        update_dict = conversation_data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            setattr(conversation, key, value)
        
        session.add(conversation)
        await session.commit()
        await session.refresh(conversation)
        return conversation

    async def delete_conversation(self, conversation: Conversation, session: AsyncSession):
        """
        Accept the already-fetched Conversation object to avoid a second DB round-trip.
        The router is responsible for fetching & ownership-checking before calling this.
        """
        conversation.is_deleted = True
        session.add(conversation)
        await session.commit()
        return {"message": "Conversation deleted successfully"}
