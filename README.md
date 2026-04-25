# ChatStack

A FastAPI-based chat application with AI-powered conversations, memory management, per-user token tracking, and role-based access control.

## Features

- **Chat with AI**: Context-aware conversations using OpenAI or Groq models
- **User Authentication**: Email/password registration with JWT-based authentication
- **Email Verification**: Account verification via Gmail SMTP
- **Role-Based Access**: Support for users, admins, and superadmins
- **Sliding Window Summarization**: Automatic conversation summarization to maintain context
- **Token Tracking**: Monitor token usage per conversation
- **Memory Management**: Persistent conversation history with summaries

## Tech Stack

- **Framework**: FastAPI with async/await
- **Database**: PostgreSQL with SQLModel ORM/Redis for caching
- **Authentication**: JWT tokens with role hierarchy
- **Email**: Gmail SMTP for verification
- **AI**: OpenAI / Groq API integration
- **Migrations**: Alembic

## SMTP Email Service (Gmail)

This project uses Gmail SMTP to send emails (e.g., account verification and password reset) via the SMTP protocol.

### Configuration:
- Uses Gmail with an **App Password** instead of the regular account password.
- Server: `smtp.gmail.com`
- Port: `587` with `TLS` enabled

### Limits:
- Up to **500 emails per day** for standard Gmail accounts.
- Maximum ~ **100 recipients per email**.
- No official monthly limit, but excessive usage may lead to temporary blocking.

### Notes:
- Suitable for development and small-scale projects.
- Not recommended for bulk or production-level email sending.
- For large-scale applications, consider using dedicated email services (Email APIs).


## AI Integration (OpenAI / Groq)

This project integrates with OpenAI-compatible APIs (OpenAI or Groq) to generate assistant responses in conversations.

### Configuration:
- Supports both **OpenAI** and **Groq** models via environment variables:
  - `OPENAI_MODEL_ID`: OpenAI model ID (e.g., `GPT-5`)
  - `GROQ_MODEL_ID`: Groq model ID (e.g., `llama-3-70b-8192`)
  - `OPENAI_BASE_URL`: Base URL for Groq (not needed for OpenAI)
  - `OPENAI_API_KEY`: API key for the selected provider
  - `SYSTEM_PROMPT`: System prompt for the AI assistant
  - `LIMIT`: Number of recent messages to keep in context (default: 10)

### Features:
- **Sliding Window Summarization**: Automatically summarizes older messages when conversation exceeds `LIMIT`, preserving context while reducing token usage.
- **Token Tracking**: Tracks `prompt_tokens`, `completion_tokens`, and `total_tokens` per conversation for usage monitoring.
- **Error Handling**: Includes retry logic for rate limits and API errors.
- **Dynamic Provider Selection**: Automatically selects OpenAI or Groq based on configured model ID.

### Notes:
- Summaries are stored in the `summary` column of the `conversations` table.
- Token counts are accumulated in `prompt_tokens`, `completion_tokens`, and `total_tokens` columns.
- Suitable for chat applications with context-aware AI responses.