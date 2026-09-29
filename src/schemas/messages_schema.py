from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List
from .enums.role_enum import MessageRole

class MessageBase(BaseModel):
    role: MessageRole
    content: str
    image_urls: Optional[List[str]] = None

class MessageCreate(BaseModel):
    conversation_id: int
    content: str
    image_urls: Optional[List[str]] = None

class MessageRead(MessageBase):
    id: int
    conversation_id: int
    created_at: datetime

    class Config:
        from_attributes = True

class MessageResponse(BaseModel):
    message: MessageRead