import sys
import os
from sqlmodel import create_engine, SQLModel
from sqlalchemy.ext.asyncio import AsyncEngine
from helpers.config import get_settings

# Add parent (src) to path for absolute imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

settings = get_settings() # data from environment variables

engine = AsyncEngine(
    create_engine(
        url=settings.DATABASE_URL,
        echo=True
    )
)

async def init_db():
    async with engine.begin() as conn:
        from models import (User, Message, Conversation, MessageMetadata)
        await conn.run_sync(SQLModel.metadata.create_all) # Creates all registered tables
