import logging
from typing import List, Dict
from openai import (
    AsyncOpenAI, RateLimitError,
    APIError, APITimeoutError,
)
from utils.errors import AIClientError, AIRateLimitError
from utils.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)

SYSTEM_PROMPT = settings.SYSTEM_PROMPT


def get_ai_client() -> AsyncOpenAI:
    """Return an AsyncOpenAI client configured from application settings."""
    # Auto-detect provider: Groq needs custom base_url, OpenAI uses default
    if settings.OPENAI_MODEL_ID:
        base_url = None
    elif settings.GROQ_MODEL_ID:
        base_url = settings.OPENAI_BASE_URL or None
    else:
        base_url = settings.OPENAI_BASE_URL or None

    return AsyncOpenAI(
        api_key=settings.OPENAI_API_KEY,
        base_url=base_url,
        timeout=30.0,
    )

async def generate_chat_response(
    messages: List[Dict[str, str]],
    max_retries: int = 3) -> str:
    """
    Send messages to the configured LLM and return the assistant's text response.

    Args:
        messages: OpenAI-style message list (role/content dicts).
        max_retries: Number of retries on transient errors.
    Returns:
        The assistant's reply content.
    Raises:
        AIClientError: On fatal API or network failures.
        AIRateLimitError: When rate-limited after retries.
    """

    client = get_ai_client()
    model = settings.OPENAI_MODEL_ID or settings.GROQ_MODEL_ID

    if not model:
        logger.error("No model ID configured (OPENAI_MODEL_ID or GROQ_MODEL_ID)")
        raise AIClientError("LLM model ID is not configured")

    # Prepend system prompt
    openai_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    openai_messages.extend(messages)

    last_exception = None
    for attempt in range(1, max_retries + 1):
        try:
            response = await client.chat.completions.create(
                model= model,
                messages= openai_messages,
                temperature= 0.3,
            )
            content = response.choices[0].message.content
            if content is None:
                logger.warning("LLM returned empty content")
                return ""
            return content

        except RateLimitError as exc:
            logger.warning(f"Rate limit hit (attempt {attempt}/{max_retries}): {exc}")
            last_exception = exc
            continue

        except (APITimeoutError, APIError) as exc:
            logger.warning(f"LLM API error (attempt {attempt}/{max_retries}): {exc}")
            last_exception = exc
            continue

        except Exception as exc:
            logger.exception(f"Unexpected error calling LLM (attempt {attempt}/{max_retries})")
            last_exception = exc
            continue

    # All retries exhausted
    if isinstance(last_exception, RateLimitError):
        raise AIRateLimitError()
    raise AIClientError(str(last_exception))
