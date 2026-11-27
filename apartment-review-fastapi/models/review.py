from sqlmodel import SQLModel, Field, Index
from sqlalchemy import UniqueConstraint
from uuid import UUID, uuid4
from datetime import datetime
from typing import Optional


class Review(SQLModel, table=True):
    __tablename__ = "review"
    __table_args__ = (
        UniqueConstraint("apartment_uid", "user_uid", name="uq_review_apartment_user"),
        Index("idx_review_apartment", "apartment_uid"),
        Index("idx_review_user", "user_uid"),
    )

    uid: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    apartment_uid: UUID = Field(
        foreign_key="apartment.uid", index=True, description="Reference to apartment"
    )
    user_uid: UUID = Field(
        foreign_key="user.uid",
        index=True,
        description="Reference to user who wrote the review",
    )

    # Review content
    title: Optional[str] = Field(
        default=None, max_length=255, description="Review title/summary"
    )
    content: Optional[str] = Field(default=None, description="Detailed review text")

    # Category-specific ratings (optional)
    landlord_rating: Optional[int] = Field(
        default=None, ge=0, le=100, description="Landlord/management rating, 0 to 100"
    )
    location_rating: Optional[int] = Field(
        default=None, ge=0, le=100, description="Location rating, 0 to 100"
    )
    condition_rating: Optional[int] = Field(
        default=None, ge=0, le=100, description="Apartment condition rating, 0 to 100"
    )
    quietness_rating: Optional[int] = Field(
        default=None, ge=0, le=100, description="Quietness rating, 0 to 100"
    )

    # Only published reviews are shown to visitors
    status: str = Field(
        default="pending", max_length=20, description="pending, published or rejected"
    )

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
