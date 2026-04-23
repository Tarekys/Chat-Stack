# Request → Middleware → Endpoint → Middleware → Response

from fastapi import FastAPI
from fastapi.requests import Request
from fastapi.middleware.cors import CORSMiddleware
import time
import logging

logger = logging.getLogger("uvicorn.error")

def setup_middleware(app: FastAPI):

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def custom_logging(request: Request, call_next):
        start_time = time.time()

        response = await call_next(request)
        process_time = time.time() - start_time

        message = (
            f"{request.method} {request.url.path} "
            f"- status_code:{response.status_code} "
            f"- Completed in {process_time:.4f}s"
        )
        logger.info(message)
        return response
