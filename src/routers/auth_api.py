from fastapi import APIRouter, Depends, status
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse
from datetime import datetime

from utils.auth import create_access_token
from utils.config import get_settings
from utils.dependencies import RefreshTokenBearer

auth_router = APIRouter(
    prefix="/api/auth",
    tags=["auth"]
)
settings = get_settings()

@auth_router.get("/refresh_token")
async def new_access_token(
    token_details: dict = Depends(RefreshTokenBearer())
    ):

    expiry_timestamp = token_details['exp']
    if datetime.fromtimestamp(expiry_timestamp) > datetime.now():
        new_access_token = create_access_token(
            user_data = token_details['user']
        )

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message": "New access token generated",
                "access_token": new_access_token
            }
        )
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Token has expired or is invalid"
    )

