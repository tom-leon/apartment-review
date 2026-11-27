from sqlmodel import SQLModel, Field
from uuid import UUID, uuid4
from datetime import datetime


class User(SQLModel, table=True):
    __tablename__ = "user"

    uid: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    name: str = Field(index=True)
    email: str = Field(index=True)
    google_sub: str = Field(
        unique=True, index=True, description="Google's permanent ID for the account"
    )
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
