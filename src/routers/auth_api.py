from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from datetime import datetime
from sqlmodel.ext.asyncio.session import AsyncSession

from utils.auth.auth import create_access_token
from utils.config import get_settings
from utils.auth.dependencies import RefreshTokenBearer,RoleChecker
from controllers.users_ctrl import UserCtrl
from db.main import get_session 
from utils.errors import UserNotFound, InvalidToken, MustRoles, CannotModifySuperadmin


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
    raise InvalidToken()

@auth_router.post("/update_role", status_code=status.HTTP_200_OK)
async def update_user_role(
    email: str,
    role: str,
    session: AsyncSession = Depends(get_session),
    _: bool = Depends(role_allowed)):

    if role not in ("user", "admin"):
        raise MustRoles()

    user = await user_ctrl.get_user(email, session)
    if not user:
        raise UserNotFound()

    if user.role == "superadmin":
        raise CannotModifySuperadmin()

    user.role = role
    session.add(user)
    await session.commit()
    await session.refresh(user)

    return JSONResponse(
        content={"message": f"User '{email}' role updated to '{role}'"},
        status_code=status.HTTP_200_OK
        )
