from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi import HTTPException, status
from sqlmodel import select, desc

from models.users import User
from schemas.users_schema import UserCreate, UserUpdate
from helpers.auth import hash_password

class UserCtrl:
    async def get_all_users(self, session: AsyncSession):

        stat = select(User).order_by(desc(User.created_at))
        result = await session.exec(stat)
        return result.all()

    async def get_user(self, email: str, session: AsyncSession):

        stat = select(User).where(User.email == email)
        result = await session.exec(stat)
        user = result.first()
        return user

    async def user_exists(self, email: str, session: AsyncSession):
        user = await self.get_user(email, session)
        return True if user else False

    async def create_user(self, user_data: UserCreate, session: AsyncSession):

        user_dict = user_data.model_dump()

        # نستخرج password قبل إنشاء الـ User لأن الحقل في الـ model هو hash_password
        plain_password = user_dict.pop("password")
        new_user = User(**user_dict)
        new_user.hash_password = hash_password(plain_password)

        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)
        return new_user

    async def update_user(self, email: str, user_data: UserUpdate, session: AsyncSession):

        user_update = await self.get_user(email, session)

        if not user_update:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with email '{email}' not found"
            )

        user_update_dict = user_data.model_dump(exclude_unset=True)

        if "password" in user_update_dict:
            user_update_dict["hash_password"] = hash_password(user_update_dict.pop("password"))

        for key, value in user_update_dict.items():
            setattr(user_update, key, value)

        session.add(user_update)
        await session.commit()
        await session.refresh(user_update)
        return user_update

    async def delete_user(self, email: str, session: AsyncSession):
        
        user_delete = await self.get_user(email, session)

        if user_delete:
            await session.delete(user_delete)
            await session.commit()
            return {"message": "User deleted successfully"}
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
