from sqlmodel import SQLModel, Field
from sqlalchemy import UniqueConstraint
from uuid import UUID, uuid4
from datetime import datetime
from typing import Optional


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

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
