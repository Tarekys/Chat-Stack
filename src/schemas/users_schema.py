from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional
import uuid

# User Base Schema/ common fields for all user schemas
class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserRead(UserBase):
    id: uuid.UUID
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    hash_password: Optional[str] = None
    is_active: Optional[bool] = None