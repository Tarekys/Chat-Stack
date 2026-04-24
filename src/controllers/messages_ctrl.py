from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi import HTTPException, status
from sqlmodel import select, desc

from models.messages import Message
from schemas.messages_schema import (
    MessageCreate
)
from utils.errors import MessageNotFound

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
            raise MessageNotFound()
            
        return message

    async def create_message(self, message_data: MessageCreate, session: AsyncSession):

        # 1. Save user message
        user_msg = Message(
            conversation_id=message_data.conversation_id,
            role="user",
            content=message_data.content
        )
        session.add(user_msg)

        # TODO: Call LLM API here instead of mock response
        assistant_content = f"I received your message: '{message_data.content}'"

        # 2. Save assistant response
        assistant_msg = Message(
            conversation_id=message_data.conversation_id,
            role="assistant",
            content=assistant_content
        )
        session.add(assistant_msg)

        await session.commit()
        await session.refresh(assistant_msg)
        return assistant_msg
