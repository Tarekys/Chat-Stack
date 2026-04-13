from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional
import uuid

class ConversationBase(BaseModel):
    title: Optional[str] = None

class ConversationCreate(ConversationBase):
    user_id: uuid.UUID

class ConversationRead(ConversationBase):
    id: int
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    is_deleted: bool

    class Config:
        from_attributes = True

class ConversationUpdate(BaseModel):
    title: Optional[str] = None
    is_deleted: Optional[bool] = False