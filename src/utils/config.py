from pydantic_settings import BaseSettings
from typing import Literal
import os

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str

    APP_DOMAIN: str = "localhost:8000"
    FRONTEND_URL: str = "http://127.0.0.1:5500/UI/index.html"

    # AI Backend Configuration
    LIST_OF_AI_BACKEND: list[Literal["OPENAI", "GROQ"]] = []
    AI_BACKEND: str = None

    # APIs Keys
    OPENAI_API_KEY: str = None
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    GROQ_API_KEY: str = None
    GROQ_BASE_URL: str = "https://api.groq.com/openai/v1"

    # Models
    LIST_OF_GENERATION_MODEL: list[str] = []
    SYSTEM_PROMPT: str = None

    OPENAI_MODEL_ID: str = None
    GROQ_MODEL_ID: str = None

    # JWT
    JWT_ALGORITHM: str = None
    JWT_SECRET_KEY: str = None
    ACCESS_TOKEN_EXPIRY: int = 3600
    REFRESH_TOKEN_EXPIRY: int = 2

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379

    # Admin
    ADMIN_EMAIL: str = None
    ADMIN_USERNAME: str = None

    # Mail Service
    MAIL_USERNAME: str = None
    MAIL_PASSWORD: str = None
    MAIL_FROM: str = None
    MAIL_PORT: int = 587
    MAIL_SERVER: str = None
    MAIL_FROM_NAME: str = None

    class Config:
        env_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')

def get_settings():
    return Settings()