from fastapi import APIRouter, Depends, status
from fastapi.exceptions import HTTPException
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import List

from db.main import get_session
from controllers.users_ctrl import UserCtrl
from schemas.users_schema import UserCreate, UserUpdate, UserRead, UserResponse

user_router = APIRouter(
    prefix="/api/users",
    tags=["signup"]
)
user_ctrl = UserCtrl()

@user_router.post("/", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user_account(
    user_data: UserCreate,
    session: AsyncSession = Depends(get_session)
):
    email = user_data.email

    user_exists = await user_ctrl.user_exists(email, session)
    if user_exists:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"User with email '{email}' already exists"
        )

    new_user = await user_ctrl.create_user(user_data, session)
    return new_user


@user_router.get("/", response_model=List[UserRead])
async def get_all_users(session: AsyncSession = Depends(get_session)):

    users = await user_ctrl.get_all_users(session)
    return users


@user_router.get("/{email}", response_model=UserRead)
async def get_user(email: str, session: AsyncSession = Depends(get_session)):

    user = await user_ctrl.get_user(email, session)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with email '{email}' not found"
        )
    return user


@user_router.put("/{email}", response_model=UserRead)
async def update_user(
    email: str,
    user_data: UserUpdate,
    session: AsyncSession = Depends(get_session)):

    updated_user = await user_ctrl.update_user(email, user_data, session)
    return updated_user


@user_router.delete("/{email}", response_model=UserResponse)
async def delete_user(email: str, session: AsyncSession = Depends(get_session)):

    result = await user_ctrl.delete_user(email, session)
    return result
