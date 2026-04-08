from sqlmodel import SQLModel, Field, Column, Relationship
from datetime import datetime
from typing import Optional
import uuid
import sqlalchemy.dialects.postgresql as pg
from sqlalchemy import ForeignKey

class MessageMetadata(SQLModel, table=True):
    __tablename__ = "message_metadata"
     
    id: uuid.UUID = Field(
        sa_column= Column(pg.UUID(as_uuid=True), nullable=False, primary_key=True),
        default= uuid.uuid4)

    message_id: uuid.UUID = Field(
        sa_column= Column(pg.UUID(as_uuid=True), ForeignKey("messages.id", ondelete="CASCADE"), nullable=False, unique=True))

    model_name : str
    tokens_used : int
    response_time_ms : float
    created_at : datetime

    # One-to-One: Metadata -> Message
    message: Optional["Message"] = Relationship(back_populates="message_metadata")

    def __repr__(self):
        return f"<MessageMetadata(id={self.id}, message_id={self.message_id})>"