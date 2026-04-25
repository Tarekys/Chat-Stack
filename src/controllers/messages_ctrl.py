from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi import HTTPException, status
from sqlmodel import select, desc

from models.messages import Message
from schemas.messages_schema import (
    MessageCreate
)
from utils.errors import MessageNotFound
from utils.ai_client import generate_chat_response

LIMIT = 10

class MessageCtrl:
    async def get_messages_for_conversation(self, conversation_id: int, session: AsyncSession, limit: int = None):

        stat = select(Message).where(Message.conversation_id == conversation_id).order_by(desc(Message.created_at))
        if limit:
            stat = stat.limit(limit)
        result = await session.exec(stat)
        messages = result.all()

        # Reverse so oldest comes first (required for OpenAI conversation context)
        return list(reversed(messages))

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
        await session.commit()
        await session.refresh(user_msg)

        # 2. Fetch last N messages for context (oldest first)/ Sliding Window
        history = await self.get_messages_for_conversation(
            message_data.conversation_id, session, limit=LIMIT
        )

        # 3. Build OpenAI message list
        openai_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in history
        ]

        # 4. Call LLM
        assistant_content = await generate_chat_response(openai_messages)

        # 5. Save assistant response
        assistant_msg = Message(
            conversation_id=message_data.conversation_id,
            role="assistant",
            content=assistant_content
        )
        session.add(assistant_msg)
        await session.commit()
        await session.refresh(assistant_msg)
        return assistant_msg
