from sqlmodel import SQLModel, Field, Column, Relationship
from datetime import datetime
from typing import List, Optional, TYPE_CHECKING
import uuid
import sqlalchemy.dialects.postgresql as pg
from sqlalchemy import ForeignKey

if TYPE_CHECKING:
    from .users import User
    from .messages import Message

class Conversation(SQLModel, table=True):
    __tablename__ = "conversations"

    id: int = Field(sa_column=Column(pg.INTEGER, primary_key=True, autoincrement=True, index=True))

    user_id: uuid.UUID = Field(
        sa_column=Column(pg.UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    )
    title: str = Field(default=None)
    is_deleted: bool = Field(default=False)

    created_at: datetime = Field(sa_column= Column(pg.TIMESTAMP, default=datetime.now))
    updated_at: datetime = Field(sa_column= Column(pg.TIMESTAMP, default=datetime.now))

    # Many-to-One: Conversation -> User
    user: Optional["User"] = Relationship(back_populates="conversations")

    # One-to-Many: Conversation -> Messages
    messages: List["Message"] = Relationship(
        back_populates="conversation", # relationship with "conversation" column(figuratively)
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )

    def __repr__(self):
        return f"<Conversation(id={self.id}, title={self.title})>"