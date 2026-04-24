from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str

    APP_DOMAIN: str = "localhost:8000"

    # APIs Keys
    OPENAI_API_KEY: str = None
    OPENAI_BASE_URL: str = None
    
    # Models
    GENERATION_MODEL_ID: str = None

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