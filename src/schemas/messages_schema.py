from pydantic import BaseModel
from datetime import datetime
from typing import Dict, Any

class MessageBase(BaseModel):
    content: Dict[str, Any]

class MessageCreate(BaseModel):
    conversation_id: int
    user_content: str


class MessageRead(MessageBase):
    id: int
    conversation_id: int
    created_at: datetime

    class Config:
        from_attributes = True
    

class MessageResponse(BaseModel):
    message: MessageRead