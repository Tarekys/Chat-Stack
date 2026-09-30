from pydantic import BaseModel
from datetime import datetime
from typing import Optional
import uuid

class ConversationBase(BaseModel):
    title: Optional[str] = None
    is_pinned: Optional[bool] = None


class ConversationCreate(ConversationBase):
    user_id: uuid.UUID

class ConversationRead(ConversationBase):
    id: int
    user_id: uuid.UUID
    is_pinned: bool
    is_deleted: bool
    summary: Optional[str] = None
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ConversationUpdate(BaseModel):
    title: Optional[str] = None
    is_pinned: Optional[bool] = None