from sqlmodel import SQLModel, Field, Column, Relationship
from datetime import datetime
from typing import Optional
import uuid
import sqlalchemy.dialects.postgresql as pg
from sqlalchemy import Enum, ForeignKey

class Message(SQLModel, table=True):
    __tablename__ = "messages"

    id: uuid.UUID = Field(
        sa_column= Column(pg.UUID(as_uuid=True), nullable=False, primary_key=True),
        default= uuid.uuid4
    )

    conversation_id: uuid.UUID = Field(
        sa_column= Column(pg.UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    )
    role: str = Field(
        sa_column= Column(Enum("user", "assistant", "system", name= "message_role")),
        default= "user"
    )

    content: str = Field(default=None)
    is_deleted: bool = Field(default=False)

    created_at: datetime = Field(Column(pg.TIMESTAMP, default=datetime.now))

    # Many-to-One: Message -> Conversation
    conversation: Optional["Conversation"] = Relationship(back_populates="messages")

    # One-to-One: Message -> Metadata
    message_metadata: Optional["MessageMetadata"] = Relationship(
        back_populates="message",
        sa_relationship_kwargs={"cascade": "all, delete-orphan", "uselist": False}
    )

    def __repr__(self):
        return f"<Message(id={self.id}, role={self.role})>"
