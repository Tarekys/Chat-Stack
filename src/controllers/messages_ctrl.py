from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi import HTTPException, status
from sqlmodel import select, desc

from models.messages import Message
from schemas.messages_schema import (
    MessageCreate
)

class MessageCtrl:
    async def get_messages_for_conversation(self, conversation_id: int, session: AsyncSession):

        stat = select(Message).where(Message.conversation_id == conversation_id).order_by(Message.created_at)
        result = await session.exec(stat)
        return result.all()

    async def get_message_by_id(self, message_id: int, session: AsyncSession):

        stat = select(Message).where(Message.id == message_id)
        result = await session.exec(stat)
        message = result.first()

        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Message interaction with ID {message_id} not found"
            )
        return message

    async def create_message(self, message_data: MessageCreate, session: AsyncSession):
          
        # هنا نقوم ببناء كائن الـ JSON المطلوب
        # تطبيق الاتصال بـ LLM API KEY
        interaction_content = {
            "user": message_data.user_content,
            "assistant": f"I received your message: '{message_data.user_content}'"
        }
        
        new_message = Message(
            conversation_id=message_data.conversation_id,
            content=interaction_content
        )

        session.add(new_message)
        await session.commit()
        await session.refresh(new_message)
        return new_message
