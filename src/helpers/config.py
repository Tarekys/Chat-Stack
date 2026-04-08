from pydantic_settings import BaseSettings
import os

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str

    # APIs Keys
    OPENAI_API_KEY: str = None
    OPENAI_BASE_URL: str = None
    
    # Models
    GENERATION_MODEL_ID: str = None

    class Config:
        env_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')

def get_settings():
    return Settings()