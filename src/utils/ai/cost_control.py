import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class TokenUsage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


def extract_usage(response) -> TokenUsage:
    """Extract token usage from an OpenAI API response object."""
    usage = getattr(response, "usage", None)
    if usage is None:
        return TokenUsage()
    return TokenUsage(
        prompt_tokens=usage.prompt_tokens or 0,
        completion_tokens=usage.completion_tokens or 0,
        total_tokens=usage.total_tokens or 0,
    )


def accumulate_tokens(
    conversation,
    chat_usage: TokenUsage,
    summary_usage: TokenUsage = None,
) -> None:
    """Add token counts to a Conversation ORM object (caller must commit)."""
    conversation.prompt_tokens = (conversation.prompt_tokens or 0) + chat_usage.prompt_tokens
    conversation.completion_tokens = (conversation.completion_tokens or 0) + chat_usage.completion_tokens
    conversation.total_tokens = (conversation.total_tokens or 0) + chat_usage.total_tokens

    if summary_usage:
        conversation.prompt_tokens += summary_usage.prompt_tokens
        conversation.completion_tokens += summary_usage.completion_tokens
        conversation.total_tokens += summary_usage.total_tokens
