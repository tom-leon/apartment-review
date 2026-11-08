"""
Example API endpoints showing how to use the new Apartment and Review models.

This file demonstrates best practices for:
1. Creating apartments from OSM data
2. Creating reviews with proper validation
3. Querying apartments and reviews
4. Handling duplicate reviews

You can integrate these into your main.py or create separate routers.
"""

from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from database import SessionLocal
from models import Review
from schemas import (
    OSMAddressData,
    ApartmentResponse,
    ReviewCreate,
    ReviewResponse,
)
from utils import (
    get_or_create_apartment,
    get_apartment_by_id,
    get_apartments_by_location,
    get_reviews_for_apartment,
    get_user_review_for_apartment,
)

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ============================================================================
# APARTMENT ENDPOINTS
# ============================================================================


@router.post(
    "/apartments/from-osm",
    response_model=ApartmentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_apartment_from_osm(
    osm_data: OSMAddressData, db: Session = Depends(get_db)
):
    """
    Create or get an apartment from OpenStreetMap data.

    This endpoint accepts data from the Nominatim API and creates an apartment
    record if it doesn't exist, or returns the existing one.
    """
    apartment, created = get_or_create_apartment(db, osm_data)

    return apartment


@router.get("/apartments/{apartment_uid}", response_model=ApartmentResponse)
async def get_apartment(apartment_uid: UUID, db: Session = Depends(get_db)):
    """Get a specific apartment by UID"""
    apartment = get_apartment_by_id(db, apartment_uid)

    if not apartment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Apartment with UID {apartment_uid} not found",
        )

    return apartment


@router.get("/apartments/nearby", response_model=List[ApartmentResponse])
async def get_nearby_apartments(
    latitude: float,
    longitude: float,
    radius_km: float = 1.0,
    limit: int = 50,
    db: Session = Depends(get_db),
):
    """
    Get apartments near a specific location.

    Args:
        latitude: Center latitude
        longitude: Center longitude
        radius_km: Search radius in kilometers (default: 1.0)
        limit: Maximum number of results (default: 50)
    """
    apartments = get_apartments_by_location(db, latitude, longitude, radius_km, limit)
    return apartments


# ============================================================================
# REVIEW ENDPOINTS
# ============================================================================


@router.post(
    "/reviews", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED
)
async def create_review(
    review_data: ReviewCreate,
    user_uid: UUID,  # In production, get this from authentication token
    db: Session = Depends(get_db),
):
    """
    Create a new review for an apartment.

    Note: In production, user_uid should come from the authenticated user's token,
    not from the request body.
    """
    # Check if apartment exists
    apartment = get_apartment_by_id(db, review_data.apartment_uid)
    if not apartment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Apartment with UID {review_data.apartment_uid} not found",
        )

    # Check if user already reviewed this apartment
    existing_review = get_user_review_for_apartment(
        db, review_data.apartment_uid, user_uid
    )
    if existing_review:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You have already reviewed this apartment. "
            "Use PUT to update your review.",
        )

    # Create the review
    review = Review(
        user_uid=user_uid,
        apartment_uid=review_data.apartment_uid,
        title=review_data.title,
        content=review_data.content,
        landlord_rating=review_data.landlord_rating,
        location_rating=review_data.location_rating,
        condition_rating=review_data.condition_rating,
        value_rating=review_data.value_rating,
        quietness_rating=review_data.quietness_rating,
    )

    db.add(review)
    db.commit()
    db.refresh(review)

    return review


@router.get("/apartments/{apartment_uid}/reviews", response_model=List[ReviewResponse])
async def get_apartment_reviews(
    apartment_uid: UUID, limit: int = 100, db: Session = Depends(get_db)
):
    """Get all reviews for a specific apartment"""
    # Check if apartment exists
    apartment = get_apartment_by_id(db, apartment_uid)
    if not apartment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Apartment with UID {apartment_uid} not found",
        )

    reviews = get_reviews_for_apartment(db, apartment_uid, limit)
    return reviews
