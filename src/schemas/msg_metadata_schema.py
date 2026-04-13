from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class MessageMetadataBase(BaseModel):
    model_name: Optional[str] = None
    tokens_used: Optional[int] = None
    response_time_ms: Optional[int] = None

class MessageMetadataCreate(MessageMetadataBase):
    message_id: int

class MessageMetadataRead(MessageMetadataBase):
    id: int
    message_id: int
    created_at: datetime

    class Config:
        from_attributes = True