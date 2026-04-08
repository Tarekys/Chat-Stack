from sqlmodel import create_engine
from sqlalchemy.ext.asyncio import AsyncEngine
import sys
import os

# Add parent (src) to path for absolute imports
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from helpers.config import get_settings

settings = get_settings()

engine = AsyncEngine(
    create_engine(
        url=settings.DATABASE_URL,
        echo=True
    )
)

async def init_db():
    async with engine.begin() as conn:
        from sqlalchemy import text
        stat = text("SELECT 'welcome to app';")
        result = await conn.execute(stat)
        print(result.all())