from sqlmodel import SQLModel, Field, Column, Relationship
from datetime import datetime
import uuid
from typing import List
import sqlalchemy.dialects.postgresql as pg

class User(SQLModel, table=True):
     __tablename__ = "users"

     id: uuid.UUID = Field(
          sa_column= Column(pg.UUID(as_uuid=True), nullable=False, primary_key=True),
          default= uuid.uuid4)

     email: str = Field(unique=True, nullable=False)
     hash_password: str = Field(nullable=False)
     is_active: bool = Field(default=True)
     created_at: datetime = Field(Column(pg.TIMESTAMP, default=datetime.now))
     updated_at: datetime = Field(Column(pg.TIMESTAMP, default=datetime.now))

     # One-to-Many: User -> Conversations
     conversations: List["Conversation"] = Relationship(
         back_populates="user",
         sa_relationship_kwargs={"cascade": "all, delete-orphan"}
     )

     def __repr__(self):
         return f"<User(id={self.id}, email={self.email})>"