from sqlmodel import SQLModel, Field, Column, Relationship
from datetime import datetime
import uuid
from typing import List, TYPE_CHECKING
import sqlalchemy.dialects.postgresql as pg

if TYPE_CHECKING:
    from .conversations import Conversation

class User(SQLModel, table=True):
    __tablename__ = "users"

    id: uuid.UUID = Field(
        sa_column= Column(pg.UUID(as_uuid=True), nullable=False, primary_key=True),
        default_factory= uuid.uuid4)
    
    username: str = Field(unique=True, nullable=False)
    fullname: str = Field(nullable=False)
    role: str = Field(default="user", nullable=False)

    email: str = Field(unique=True, nullable=False)
    hash_password: str = Field(nullable=False, exclude=True)
    is_verified: bool = Field(default=False)
    is_deleted: bool = Field(default=False)


    created_at: datetime = Field(sa_column= Column(pg.TIMESTAMP, default=datetime.now))
    updated_at: datetime = Field(sa_column= Column(pg.TIMESTAMP, default=datetime.now))

    # One-to-Many: User -> Conversations use List[many]
    conversations: List["Conversation"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )

    def __repr__(self):
        return f"<User(username={self.username}, email={self.email})>"