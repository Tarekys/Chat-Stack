import sys
import os

from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.orm import sessionmaker
from sqlmodel import create_engine, SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

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
        from sqlalchemy import text

        # await conn.execute(text("DROP TABLE IF EXISTS message_metadata CASCADE"))
        # await conn.execute(text("DROP TABLE IF EXISTS messages CASCADE"))
        # await conn.execute(text("DROP TABLE IF EXISTS conversations CASCADE"))
        # await conn.execute(text("DROP TABLE IF EXISTS users CASCADE"))
        # await conn.run_sync(SQLModel.metadata.create_all)

async def get_session() -> AsyncSession: # for dependency injection in logic
     Session = sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False
     )
     async with Session() as session:
          yield session