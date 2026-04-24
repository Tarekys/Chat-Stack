from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional, List
import uuid

# User Base Schema/ common fields for all user schemas
class UserBase(BaseModel):
    username: str = Field(..., min_length=3)
    email: EmailStr = Field(..., min_length=3)
    fullname: str = Field(..., min_length=3)

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

class UserRead(UserBase):
    id: uuid.UUID
    is_verified: bool
    is_deleted: bool
    created_at: datetime
    role: str = Field(default="user")

    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    username:  Optional[str]      = None
    email:     Optional[EmailStr] = None
    password:  Optional[str]      = None
    is_verified: Optional[bool]   = False

class UserResponse(BaseModel):
    message: str

class UserLogin(BaseModel):
    email: EmailStr = Field(..., min_length=3)
    password: str = Field(..., min_length=8)

class EmailData(BaseModel):
    addresses: List[EmailStr]

class ResetPassword(BaseModel):
    email: EmailStr = Field(..., min_length=3)

class ResetPasswordConfirm(BaseModel):
    new_password: str = Field(..., min_length=8)
    confirm_new_password: str = Field(..., min_length=8)