import logging
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select, desc

logger = logging.getLogger(__name__)

from models.messages import Message
from models.conversations import Conversation
from schemas.messages_schema import (
    MessageCreate
)
from utils.errors import MessageNotFound
from utils.ai.ai_client import generate_chat_response, summarize_text
from utils.ai.cost_control import accumulate_tokens, TokenUsage

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

        # 2. Fetch conversation and ALL messages for summarization check
        conv_stat = select(Conversation).where(Conversation.id == message_data.conversation_id)
        conv_result = await session.exec(conv_stat)
        conversation = conv_result.first()

        # 3. Get ALL messages ordered oldest→newest (includes the user msg just saved)
        all_messages = await self.get_messages_for_conversation(
            message_data.conversation_id, session, limit=None
        )

        openai_messages = []
        summary_usage = None

        # 4. Sliding Window + Summarization
        if len(all_messages) > LIMIT:
            # Messages beyond the recent window need summarization
            old_messages = all_messages[:-LIMIT]
            recent_messages = all_messages[-LIMIT:]

            # Build text to summarize: previous summary + old messages
            text_to_summarize = ""
            if conversation and conversation.summary:
                text_to_summarize += f"Previous conversation summary:\n{conversation.summary}\n\nNew messages to add:\n"

            for msg in old_messages:
                text_to_summarize += f"{msg.role}: {msg.content}\n"

            try:
                new_summary, summary_usage = await summarize_text(text_to_summarize)
                if conversation:
                    conversation.summary = new_summary
                    session.add(conversation)
                    await session.commit()
            except Exception as exc:
                logger.warning(f"Summarization failed, using previous summary if available: {exc}")
                summary_usage = None

            # Add summary as system context if available
            if conversation and conversation.summary:
                openai_messages.append({
                    "role": "system",
                    "content": f"Summary of earlier conversation: {conversation.summary}"
                })

            # Add recent messages verbatim
            for msg in recent_messages:
                openai_messages.append({"role": msg.role, "content": msg.content})
        else:
            # Under limit, send all messages as-is
            for msg in all_messages:
                openai_messages.append({"role": msg.role, "content": msg.content})

        # 5. Call LLM
        assistant_content, chat_usage = await generate_chat_response(openai_messages)

        # 6. Accumulate token usage in conversation
        if conversation:
            accumulate_tokens(conversation, chat_usage, summary_usage)
            session.add(conversation)

        # 7. Save assistant response
        assistant_msg = Message(
            conversation_id=message_data.conversation_id,
            role="assistant",
            content=assistant_content
        )
        session.add(assistant_msg)
        await session.commit()
        await session.refresh(assistant_msg)
        return assistant_msg
