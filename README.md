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
- **Image Support**: S3-compatible cloud storage (IDrive e2) for uploading and interacting with images

## Tech Stack

- **Framework**: FastAPI with async/await
- **Database**: PostgreSQL with SQLModel ORM/Redis for caching
- **Authentication**: JWT tokens with role hierarchy
- **Email**: Gmail SMTP for verification
- **AI**: OpenAI / Groq API integration
- **Storage**: S3-compatible API (boto3) for media
- **Migrations**: Alembic

## Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Tarekys/Chat-Stack.git
   ```

2. **Create and activate a virtual environment (e.g., using Conda):**
   ```bash
   conda create -n env_name python=3.11
   conda activate env_name
   ```

3. **Install dependencies:**
   ```bash
   cd src
   pip install -r requirements.txt
   ```

4. **Environment Variables:**
   - Copy `.env.example` to `.env` inside the `src/` directory.
   - Update the variables inside `.env` (Database URL, API Keys, JWT Secret, Mail configs).

5. **Run the Server:**
   ```bash
   uvicorn main:app --reload --port 8000
   ```
   The API will be available at `http://127.0.0.1:8000`.

## Quick Start: From Signup to Chat

1. **Sign Up**: `POST /api/users/signup` - Create a new account with email, username, and password. The system will send a verification email to the provided email address.
2. **Verify Email**: 
   - Check your email inbox for a verification email from ChatStack
   - Click the "Verify Email Address" button in the email
   - This will call `GET /api/auth/verify_email/{token}` to verify your account
3. **Login**: `POST /api/users/login` - Authenticate and receive access_token and refresh_token
4. **Create Conversation**: `POST /api/conversations/` - Start a new conversation (requires access_token in Authorization header)
5. **Send Message**: `POST /api/messages/` - Send a message to the AI in your conversation
6. **View History**: `GET /api/messages/conversation/{conversation_id}` - Get conversation history

## SMTP Email Service (Gmail)

This project uses Gmail SMTP to send emails (e.g., account verification and password reset) via the SMTP protocol.

### Configuration:
- Uses Gmail with an **App Password** instead of the regular account password.
- Server: `smtp.gmail.com`
- Port: `587` with `TLS` enabled
- Set `FRONTEND_URL` to the public URL of `UI/index.html` so password-reset emails open the UI form (the development default uses VS Code Live Server).

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