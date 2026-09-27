# Request → Middleware → Endpoint → Middleware → Response

from fastapi import FastAPI
from fastapi.requests import Request
from fastapi.middleware.cors import CORSMiddleware
from utils.config import get_settings
import time
import logging

logger = logging.getLogger("uvicorn.error")
settings = get_settings()

def setup_middleware(app: FastAPI):

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )

    @app.middleware("http")
    async def security_and_logging(request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time

        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Logging
        level = logging.WARNING if response.status_code in (401, 403, 429) else logging.INFO
        message = (
            f"{request.method} {request.url.path} "
            f"- status:{response.status_code} "
            f"- {process_time:.4f}s"
            + (f" - IP:{request.client.host}" if response.status_code in (401, 403, 429) else "")
        )
        logger.log(level, message)
        return response
