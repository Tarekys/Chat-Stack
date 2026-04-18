from sqlmodel import SQLModel, Field, Column, Relationship
from datetime import datetime
from typing import Optional, TYPE_CHECKING
import sqlalchemy.dialects.postgresql as pg
from sqlalchemy import ForeignKey

if TYPE_CHECKING:
    from .messages import Message

class MessageMetadata(SQLModel, table=True):
    __tablename__ = "msg_metadata"
     
    id: int = Field(sa_column=Column(pg.INTEGER, primary_key=True, autoincrement=True, index=True))

    message_id: int = Field(
        sa_column= Column(pg.INTEGER, ForeignKey("messages.id", ondelete="CASCADE"), nullable=False)
    )

    model_name : str
    tokens_used : int
    response_time_ms : float
    
    created_at : datetime = Field(sa_column= Column(pg.TIMESTAMP, default=datetime.now))

    # One-to-One: Metadata -> Message
    message: Optional["Message"] = Relationship(back_populates="msg_metadata")

    def __repr__(self):
        return f"<MessageMetadata(id={self.id}, message_id={self.message_id})>"