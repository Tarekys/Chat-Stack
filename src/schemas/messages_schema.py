from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from .enums.role_enum import MessageRole

class MessageBase(BaseModel):
    content: str
    role: MessageRole

class MessageCreate(MessageBase):
    conversation_id: int
    role: MessageRole

class MessageRead(MessageBase):
    id: int
    conversation_id: int
    created_at: datetime
    is_deleted: bool

    class Config:
        from_attributes = True

class MessageUpdate(BaseModel):
    content: Optional[str] = None
    role: Optional[str] = None
    is_deleted: Optional[bool] = None