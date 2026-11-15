from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import Optional


class OSMAddressData(BaseModel):
    """Schema for address data received from OpenStreetMap/Nominatim API"""

    osm_type: Optional[str] = None
    osm_id: Optional[int] = None
    osm_class: Optional[str] = Field(default=None, alias="class")

    # Address components
    street: Optional[str] = Field(default=None, alias="road")
    house_number: Optional[str] = None
    city: Optional[str] = None
    town: Optional[str] = None  # OSM sometimes uses 'town' instead of 'city'
    village: Optional[str] = None  # OSM sometimes uses 'village' instead of 'city'
    state: Optional[str] = None
    postcode: Optional[str] = None
    country: Optional[str] = None
    country_code: Optional[str] = None

    # Full address
    display_name: str

    class Config:
        populate_by_name = True

    def get_city(self) -> str:
        """Get city name, trying different OSM fields"""
        return self.city or self.town or self.village or "Unknown"


class ApartmentCreate(BaseModel):
    """Schema for creating an apartment"""

    osm_type: Optional[str] = None
    osm_id: Optional[int] = None
    osm_class: Optional[str] = None

    street: Optional[str] = None
    house_number: Optional[str] = None
    city: str
    state: Optional[str] = None
    postcode: Optional[str] = None
    country: str
    country_code: str

    display_name: str


class ApartmentResponse(BaseModel):
    """Schema for apartment response"""

    uid: UUID
    osm_type: Optional[str]
    osm_id: Optional[int]
    osm_class: Optional[str]

    street: Optional[str]
    house_number: Optional[str]
    city: str
    state: Optional[str]
    postcode: Optional[str]
    country: str
    country_code: str

    display_name: str

    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ReviewCreate(BaseModel):
    """Schema for creating a review"""

    apartment_uid: UUID
    title: Optional[str] = None
    content: Optional[str] = None

    landlord_rating: Optional[int] = Field(default=None, ge=1, le=10)
    location_rating: Optional[int] = Field(default=None, ge=1, le=10)
    condition_rating: Optional[int] = Field(default=None, ge=1, le=10)
    value_rating: Optional[int] = Field(default=None, ge=1, le=10)
    quietness_rating: Optional[int] = Field(default=None, ge=1, le=10)


class ReviewResponse(BaseModel):
    """Schema for review response"""

    uid: UUID
    apartment_uid: UUID
    user_uid: UUID

    title: Optional[str]
    content: Optional[str]

    landlord_rating: Optional[int]
    location_rating: Optional[int]
    condition_rating: Optional[int]
    value_rating: Optional[int]
    quietness_rating: Optional[int]

    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserResponse(BaseModel):
    """Schema for user response"""

    uid: UUID
    name: str
    email: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class RecentApartmentResponse(BaseModel):
    """Schema for a recently reviewed apartment on the home page"""

    uid: UUID
    house_number: Optional[str]
    street: Optional[str]
    city: str
    state: Optional[str]
    postcode: Optional[str]
    display_name: str

    review_count: int
    average_score: Optional[int]
    latest_review_text: Optional[str]
    photo_url: Optional[str]
