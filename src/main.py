import sys
import os
# Add src to path for absolute imports to run the server
sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI
from contextlib import asynccontextmanager
from db.main import init_db
from routers import (
    base_api,
    conversations_api,
    users_api,
    messages_api,
    auth_api
)

@asynccontextmanager
async def life_span(app: FastAPI): # lifespan must have async function
    print("server is starting...")
    await init_db()
    yield
    print("server is shutting down...")

app = FastAPI(
    title= "Chat App",
    description= "A chat application with memory management",
    version= "1.0"
)

app.include_router(base_api.base_router)
app.include_router(auth_api.auth_router)
app.include_router(users_api.user_router)
app.include_router(conversations_api.conv_router)
app.include_router(messages_api.messages_router)
