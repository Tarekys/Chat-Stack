from fastapi import APIRouter, Depends, status, Request
from fastapi.responses import JSONResponse
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import List
from datetime import timedelta
from db.main import get_session
from controllers.users_ctrl import UserCtrl 
from schemas.users_schema import (
    UserCreate, UserUpdate,
    UserRead, UserLogin, SingleEmailData)
from utils.config import get_settings

from utils.auth.auth import create_access_token, verify_password, generate_url_token
from utils.auth.mail import send_email
from utils.errors import UserNotFound, UserAlreadyExists, InvalidCredentials

from utils.auth.dependencies import (
    AccessTokenBearer,
    get_current_user,
    RoleChecker
)
from db.redis import add_jti_to_blocklist
from utils.templates import render_template
from slowapi import Limiter
from slowapi.util import get_remote_address

user_router = APIRouter(prefix="/api/users",tags=["users"])

limiter = Limiter(key_func=get_remote_address)
user_allowed = RoleChecker(["user"])
admin_allowed = RoleChecker(["admin"])

user_ctrl = UserCtrl()
settings = get_settings()


@user_router.post("/signup", status_code=status.HTTP_201_CREATED)
@limiter.limit("5/minute")
async def create_user_account(
    request: Request,
    user_data: UserCreate,
    session: AsyncSession = Depends(get_session)):

    email = user_data.email
    user_exists = await user_ctrl.user_exists(email, session)
    if user_exists:
        raise UserAlreadyExists()
    new_user = await user_ctrl.create_user(user_data, session)

    # Verify email token using SMTP Server
    token_data = {"email":email}
    token = generate_url_token(token_data)

    verify_link = f"http://{settings.APP_DOMAIN}/api/auth/verify_email/{token}"
    
    html_message = render_template("email_verification.html", verify_link=verify_link, username=new_user.username)
    await send_email(recipients=[email], subject="Verify Your Account", body=html_message)

    return {
        "message": "Account Created Successfully. Please check your email to verify your account.",
        "user": new_user,
    }

@user_router.post("/login", response_model=UserRead, status_code=status.HTTP_200_OK)
@limiter.limit("10/minute")
async def login_user(
    request: Request,
    user_data: UserLogin,
    session: AsyncSession = Depends(get_session)):

    email = user_data.email
    password = user_data.password

    user = await user_ctrl.get_user(email, session)

    if not user:
        raise InvalidCredentials()  # لا نُفصح إن كان السبب Email أم Password

    if not user.is_verified:
        from utils.errors import AccountNotVerified
        raise AccountNotVerified()
        
    if not verify_password(password, user.hash_password):
        raise InvalidCredentials()

    access_token = create_access_token(
        user_data={
            "email": user.email,
            "user_id": str(user.id),
            "role": user.role
        },
        expiry = timedelta(seconds=settings.ACCESS_TOKEN_EXPIRY)
    )

    refresh_token = create_access_token(
        user_data={
            "email": user.email,
            "user_id": str(user.id)
        },
        refresh = True,
        expiry = timedelta(days=settings.REFRESH_TOKEN_EXPIRY)
    )

    return JSONResponse(
        content={
            "message": "Login successful",
            "access_token": access_token,
            "refresh_token": refresh_token,
            "user_data": {
                "email": user.email,
                "user_id": str(user.id),
                "role": user.role
            }
        }
   )

@user_router.post("/resend-verification")
async def resend_verification_email(
    email_data: SingleEmailData,
    session: AsyncSession = Depends(get_session)
    ):
    email = email_data.email
    user = await user_ctrl.get_user(email, session)
    
    if not user:
        raise UserNotFound()
    
    if user.is_verified:
        return JSONResponse(
            content={"message": "Account is already verified"},
            status_code=status.HTTP_200_OK
        )
    
    # Generate new verification token and send email
    token_data = {"email": email}
    token = generate_url_token(token_data)
    verify_link = f"http://{settings.APP_DOMAIN}/api/auth/verify_email/{token}"
    html_message = render_template("email_verification.html", verify_link=verify_link, username=user.username)
    
    await send_email(recipients=[email], subject="Verify Your Account - ChatStack", body=html_message)
    
    return JSONResponse(
        content={"message": "Verification email resent successfully"},
        status_code=status.HTTP_200_OK
    )

@user_router.post("/logout", status_code=status.HTTP_200_OK)
async def revoke_token(
    token_details: dict = Depends(AccessTokenBearer())
    ):
    """Revoke the current access token (logout)."""
    jti = token_details["jti"]
    await add_jti_to_blocklist(jti)
    return JSONResponse(
        content={"message": "Logged out successfully"},
        status_code=status.HTTP_200_OK
    )


@user_router.get("/me")
async def get_my_profile(
    current_user = Depends(get_current_user),
    _: bool = Depends(user_allowed)
    ):
    """Get the authenticated user's profile."""
    return current_user


@user_router.put("/me", response_model=UserRead)
async def update_my_profile(
    user_data: UserUpdate,
    session: AsyncSession = Depends(get_session),
    current_user = Depends(get_current_user),
    _: bool = Depends(user_allowed)
    ):
    """Update the authenticated user's own profile."""
    updated_user = await user_ctrl.update_user(current_user.email, user_data, session)
    return updated_user


@user_router.delete("/me", status_code=status.HTTP_200_OK)
async def delete_my_account(
    session: AsyncSession = Depends(get_session),
    current_user = Depends(get_current_user),
    _: bool = Depends(user_allowed)
    ):
    """Soft-delete the authenticated user's own account."""
    result = await user_ctrl.delete_user(current_user.email, session)
    return JSONResponse(content=result, status_code=status.HTTP_200_OK)


@user_router.get("/all", response_model=List[UserRead])
async def get_all_users(
    session: AsyncSession = Depends(get_session),
    _: bool = Depends(admin_allowed)
    ):
    
    users = await user_ctrl.get_all_users(session)
    return users


# @user_router.get("/{email}", response_model=UserRead)
# async def get_user(email: str, session: AsyncSession = Depends(get_session)):
    
#     user = await user_ctrl.get_user(email, session)
#     if not user:
#         raise UserNotFound()
#     return user


# @user_router.put("/update/{email}", response_model=UserRead)
# async def update_user(
#     email: str,
#     user_data: UserUpdate,
#     session: AsyncSession = Depends(get_session)):

#     updated_user = await user_ctrl.update_user(email, user_data, session)
#     return updated_user


# # @user_router.delete("/delete/{email}", response_model=UserResponse)
# # async def delete_user(email: str, session: AsyncSession = Depends(get_session)):

#     result = await user_ctrl.delete_user(email, session)
#     return result