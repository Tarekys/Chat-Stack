from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi import HTTPException, status
from sqlmodel import select, desc

from models.conversations import Conversation
from schemas.conversations_schema import (
    ConversationCreate,
    ConversationUpdate
)

class ConversationCtrl:
    async def get_all_conversations(self, session: AsyncSession):
        
        stat = select(Conversation).where(Conversation.is_deleted == False).order_by(desc(Conversation.created_at))
        result = await session.exec(stat)
        return result.all()

    async def get_conversation(self, conversation_id: int, session: AsyncSession):
        
        stat = select(Conversation).where(Conversation.id == conversation_id, Conversation.is_deleted == False)
        result = await session.exec(stat)
        conv = result.first()

        if not conv:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail=f"Conversation with ID {conversation_id} not found"
            )
        return conv

    async def create_conversation(self, conversation_data: ConversationCreate, session: AsyncSession):
        
        conv_dict = conversation_data.model_dump()
        new_conv = Conversation(**conv_dict)

        session.add(new_conv)
        await session.commit()
        await session.refresh(new_conv)
        return new_conv

    async def update_conversation(self, conversation_id: int, conversation_data: ConversationUpdate, session: AsyncSession):
        
        conv_update = await self.get_conversation(conversation_id, session)
        update_dict = conversation_data.model_dump(exclude_unset=True)

        for key, value in update_dict.items():
            setattr(conv_update, key, value)
        
        session.add(conv_update)
        await session.commit()
        await session.refresh(conv_update)
        return conv_update

    async def delete_conversation(self, conversation_id: int, session: AsyncSession):
        
        conv_delete = await self.get_conversation(conversation_id, session)
        
        conv_delete.is_deleted = True
        session.add(conv_delete)
        await session.commit()
        return {"message": "Conversation deleted successfully"}