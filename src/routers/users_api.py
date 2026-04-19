from fastapi import APIRouter, Depends, status
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import List
from datetime import timedelta, datetime

from db.main import get_session
from controllers.users_ctrl import UserCtrl 
from schemas.users_schema import (
    UserCreate, UserUpdate,
    UserRead, UserResponse, UserLogin)

from utils.auth import create_access_token, decode_token, verify_password
from utils.config import get_settings
from utils.dependencies import RefreshTokenBearer, AccessTokenBearer

user_router = APIRouter(
    prefix="/api/users",
    tags=["auth"]
)
user_ctrl = UserCtrl()
settings = get_settings()


@user_router.post("/signup", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user_account(
    user_data: UserCreate,
    session: AsyncSession = Depends(get_session)):

    email = user_data.email
    user_exists = await user_ctrl.user_exists(email, session)
    if user_exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User with email '{email}' already exists"
        )

    new_user = await user_ctrl.create_user(user_data, session)
    return new_user


@user_router.post("/login", response_model=UserRead, status_code=status.HTTP_200_OK)
async def login_user(
    user_data: UserLogin,
    session: AsyncSession = Depends(get_session)):

    email = user_data.email
    password = user_data.password

    user = await user_ctrl.get_user(email, session)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with email '{email}' not found"
        )
    if user:
        password_vaild = verify_password(password, user.hash_password)

        if password_vaild:
            access_token = create_access_token(
                user_data={
                    "email": user.email,
                    "user_id": str(user.id)
                },
                expiry = timedelta(seconds=settings.ACCESS_TOKEN_EXPIRY)
            )

            refresh_token = create_access_token(
                user_data={
                    "email": user.email,
                    "user_id": str(user.id)
                },
                refresh = True,
                expiry = timedelta(days=settings.REFRESH_TOEKN_EXPIRY)
            )

            return JSONResponse(
                content={
                    "message": "Login successful",
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "user_data": {
                        "email": user.email,
                        "user_id": str(user.id)
                    }
                }
           )

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid credentials, Email or password is incorrect"
    )


@user_router.get("/all", response_model=List[UserRead])
async def get_all_users(session: AsyncSession = Depends(get_session)):
    
    users = await user_ctrl.get_all_users(session)
    return users

@user_router.get("/refresh_token")
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


# @user_router.get("/{email}", response_model=UserRead)
# async def get_user(email: str, session: AsyncSession = Depends(get_session)):
    
#     user = await user_ctrl.get_user(email, session)
#     if not user:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail=f"User with email '{email}' not found"
#         )
#     return user


# @user_router.put("/update/{email}", response_model=UserRead)
# async def update_user(
#     email: str,
#     user_data: UserUpdate,
#     session: AsyncSession = Depends(get_session)):

#     updated_user = await user_ctrl.update_user(email, user_data, session)
#     return updated_user


# @user_router.delete("/delete/{email}", response_model=UserResponse)
# async def delete_user(email: str, session: AsyncSession = Depends(get_session)):

#     result = await user_ctrl.delete_user(email, session)
#     return result