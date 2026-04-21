from fastapi import APIRouter, Depends, status
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse
from datetime import datetime
from sqlmodel.ext.asyncio.session import AsyncSession

from utils.auth import create_access_token
from utils.config import get_settings
from utils.dependencies import RefreshTokenBearer,RoleChecker
from controllers.users_ctrl import UserCtrl
from db.main import get_session 

auth_router = APIRouter(prefix="/api/auth",tags=["auth"])

role_allowed = RoleChecker(["superadmin"])
user_ctrl = UserCtrl()
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

@auth_router.post("/update_role", status_code=status.HTTP_200_OK)
async def update_user_role(
    email: str,
    role: str,
    session: AsyncSession = Depends(get_session),
    _: bool = Depends(role_allowed)):

    if role not in ("user", "admin"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role must be 'user' or 'admin'"
        )
    user = await user_ctrl.get_user(email, session)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with email '{email}' not found"
        )
    if user.role == "superadmin":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot modify superadmin role"
        )
    user.role = role
    session.add(user)
    await session.commit()
    await session.refresh(user)

    return JSONResponse(
        content={"message": f"User '{email}' role updated to '{role}'"},
        status_code=status.HTTP_200_OK
        )
