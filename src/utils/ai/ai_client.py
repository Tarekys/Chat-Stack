import logging
from typing import List, Dict, Tuple, Any
# pyrefly: ignore [missing-import]
from openai import (
    AsyncOpenAI, RateLimitError,
    APIError, APITimeoutError,
)
from utils.errors import AIClientError, AIRateLimitError
from utils.config import get_settings
from utils.ai.cost_control import TokenUsage, extract_usage

settings = get_settings()
logger = logging.getLogger(__name__)

SYSTEM_PROMPT = settings.SYSTEM_PROMPT


def get_ai_client() -> AsyncOpenAI:
    """Return an AsyncOpenAI client configured from application settings based on AI_BACKEND."""
    if settings.AI_BACKEND == "GROQ":
        api_key = settings.GROQ_API_KEY
        base_url = settings.BASE_URL
    else:  # OPENAI
        api_key = settings.OPENAI_API_KEY

    return AsyncOpenAI(
        api_key=api_key,
        base_url=base_url,
        timeout=30.0,
    )

async def generate_chat_response(
    messages: List[Dict[str, Any]],
    max_retries: int = 3) -> Tuple[str, TokenUsage]:
    """
    Send messages to the configured LLM and return the assistant's text response + token usage.

    Args:
        messages: OpenAI-style message list (role/content dicts).
        max_retries: Number of retries on transient errors.
    Returns:
        Tuple of (assistant reply content, TokenUsage).
    Raises:
        AIClientError: On fatal API or network failures.
        AIRateLimitError: When rate-limited after retries.
    """

    client = get_ai_client()
    
    if settings.AI_BACKEND == "GROQ":
        model = settings.GROQ_MODEL_ID
        if not model:
            logger.error("GROQ_MODEL_ID is not configured for GROQ backend")
            raise AIClientError("GROQ_MODEL_ID is not configured")
    else:  # OPENAI
        model = settings.OPENAI_MODEL_ID
        if not model:
            logger.error("OPENAI_MODEL_ID is not configured for OpenAI backend")
            raise AIClientError("OPENAI_MODEL_ID is not configured")

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
            usage = extract_usage(response)
            if content is None:
                logger.warning("LLM returned empty content")
                return "", usage
            return content, usage

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


async def summarize_text(text_to_summarize: str, max_retries: int = 2) -> Tuple[str, TokenUsage]:
    """
    Summarize a block of text (conversation history) using the configured LLM.
    Returns:
        Tuple of (concise summary string, TokenUsage).
    Raises:
        AIClientError: If summarization fails after retries.
    """
    client = get_ai_client()
    
    if settings.AI_BACKEND == "GROQ":
        model = settings.GROQ_MODEL_ID
        if not model:
            logger.error("GROQ_MODEL_ID is not configured for summarization with GROQ backend")
            raise AIClientError("GROQ_MODEL_ID is not configured")
    else:  # OPENAI
        model = settings.OPENAI_MODEL_ID
        if not model:
            logger.error("OPENAI_MODEL_ID is not configured for summarization with OpenAI backend")
            raise AIClientError("OPENAI_MODEL_ID is not configured")

    messages = [
        {"role": "system", "content": "You are a summarization assistant. Summarize the following conversation,while preserving key facts, decisions, and context."},
        {"role": "user", "content": text_to_summarize},
    ]

    last_exception = None
    for attempt in range(1, max_retries + 1):
        try:
            response = await client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.3,
                max_tokens=512,
            )
            content = response.choices[0].message.content
            usage = extract_usage(response)
            if content is None:
                return "", usage
            return content.strip(), usage

        except (RateLimitError, APITimeoutError, APIError) as exc:
            logger.warning(f"Summarization API error (attempt {attempt}/{max_retries}): {exc}")
            last_exception = exc
            continue
        except Exception as exc:
            logger.exception(f"Unexpected summarization error (attempt {attempt}/{max_retries})")
            last_exception = exc
            continue

    if isinstance(last_exception, RateLimitError):
        raise AIRateLimitError()
    raise AIClientError(str(last_exception))
