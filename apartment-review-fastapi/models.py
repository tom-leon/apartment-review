from sqlmodel import SQLModel, Field, Column, Index
from sqlalchemy import UniqueConstraint, DECIMAL
from uuid import UUID, uuid4
from datetime import datetime
from typing import Optional
from decimal import Decimal


class User(SQLModel, table=True):
    __tablename__ = "user"

    uid: UUID = Field(default_factory=uuid4, primary_key=True, index=True)
    name: str = Field(index=True)
    email: str = Field(unique=True, index=True)
    password: str
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Apartment(SQLModel, table=True):
    __tablename__ = "apartment"
    __table_args__ = (
        UniqueConstraint(
            "street",
            "house_number",
            "city",
            "postcode",
            "country_code",
            name="uq_apartment_address",
        ),
        Index("idx_apartment_location", "latitude", "longitude"),
    )

    uid: UUID = Field(default_factory=uuid4, primary_key=True, index=True)

    # OSM reference data (for linking back to map)
    osm_type: Optional[str] = Field(
        default=None,
        max_length=20,
        description="OSM object type: node, way, or relation",
    )
    osm_id: Optional[int] = Field(default=None, description="OpenStreetMap object ID")
    osm_class: Optional[str] = Field(
        default=None, max_length=50, description="OSM class: building, place, etc."
    )

    # Address components (normalized from OSM)
    street: Optional[str] = Field(default=None, max_length=255, index=True)
    house_number: Optional[str] = Field(default=None, max_length=50)
    city: str = Field(max_length=100, index=True)
    state: Optional[str] = Field(default=None, max_length=100)
    postcode: Optional[str] = Field(default=None, max_length=20, index=True)
    country: str = Field(max_length=100)
    country_code: str = Field(
        max_length=2, index=True, description="ISO 3166-1 alpha-2 country code"
    )

    # Full address for display
    display_name: str = Field(description="Full formatted address from OSM")

    # Coordinates - using DECIMAL for precision
    latitude: Decimal = Field(
        sa_column=Column(DECIMAL(10, 8), nullable=False),
        description="Latitude coordinate",
    )
    longitude: Decimal = Field(
        sa_column=Column(DECIMAL(11, 8), nullable=False),
        description="Longitude coordinate",
    )

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


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
        default=None, ge=1, le=10, description="Landlord/management rating from 1 to 10"
    )
    location_rating: Optional[int] = Field(
        default=None, ge=1, le=10, description="Location rating from 1 to 10"
    )
    condition_rating: Optional[int] = Field(
        default=None, ge=1, le=10, description="Apartment condition rating from 1 to 10"
    )
    quietness_rating: Optional[int] = Field(
        default=None, ge=1, le=10, description="Quietness rating from 1 to 10"
    )

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
