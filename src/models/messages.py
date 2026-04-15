from sqlmodel import SQLModel, Field, Column, Relationship
from datetime import datetime
from typing import Optional, TYPE_CHECKING, Dict, Any
import sqlalchemy.dialects.postgresql as pg
from sqlalchemy import ForeignKey


if TYPE_CHECKING:
    from .conversations import Conversation
    from .msg_metadata import MessageMetadata

class Message(SQLModel, table=True):
    __tablename__ = "messages"

    id: int = Field(sa_column= Column(pg.INTEGER, primary_key=True, autoincrement=True, index=True))

    conversation_id: int = Field(
        sa_column= Column(pg.INTEGER, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    )

    content: Dict[str, Any] = Field(sa_column= Column(pg.JSONB), default={})
    created_at: datetime = Field(sa_column= Column(pg.TIMESTAMP, default=datetime.now))

    # Many-to-One: Message -> Conversation
    conversation: Optional["Conversation"] = Relationship(back_populates="messages")

    # One-to-One: Message -> Metadata
    msg_metadata: Optional["MessageMetadata"] = Relationship(
        back_populates="message",
        sa_relationship_kwargs={"cascade": "all, delete-orphan", "uselist": False}
    )

    def __repr__(self):
        return f"<Message(id={self.id}, interaction={self.content})>"
