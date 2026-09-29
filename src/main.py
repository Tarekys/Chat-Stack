import sys
import os
# Add src to path for absolute imports to run the server
sys.path.insert(0, os.path.dirname(__file__))

# pyrefly: ignore [missing-import]
from fastapi import FastAPI
from contextlib import asynccontextmanager
from db.main import init_db
from utils.errors import register_all_errors
from utils.middleware import setup_middleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from routers import (
    base_api,
    conversations_api,
    users_api,
    messages_api,
    auth_api,
    s3_api
)

@asynccontextmanager
async def life_span(app: FastAPI): # lifespan must have async function
    print("server is starting...")
    await init_db()
    yield
    print("server is shutting down...")

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title= "Chat App",
    description= "A chat application with memory management",
    version= "1.0",
    lifespan=life_span
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

register_all_errors(app)

setup_middleware(app)

app.include_router(base_api.base_router)
app.include_router(auth_api.auth_router)
app.include_router(users_api.user_router)
app.include_router(conversations_api.conv_router)
app.include_router(messages_api.messages_router)
app.include_router(s3_api.s3_router)
