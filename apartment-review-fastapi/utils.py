from datetime import datetime
from enum import Enum
from returns.result import Failure, Result, Success, safe
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from models import Apartment, Review
from photos import street_view_photo_url
from schemas import OSMAddressData, RecentApartmentResponse, ReviewUpdate
from typing import Optional, Tuple
from uuid import UUID


def get_or_create_apartment(
    db: Session, osm_data: OSMAddressData
) -> Tuple[Apartment, bool]:
    """
    Get an existing apartment or create a new one based on OSM address data.

    Args:
        db: Database session
        osm_data: Address data from OpenStreetMap/Nominatim

    Returns:
        Tuple of (Apartment, created) where created is True if a new apartment
        was created
    """
    # Normalize address components for lookup
    city = osm_data.get_city()
    country_code = (osm_data.country_code or "").upper()

    # Try to find existing apartment by normalized address
    existing = (
        db.query(Apartment)
        .filter(
            Apartment.street == osm_data.street,
            Apartment.house_number == osm_data.house_number,
            Apartment.city == city,
            Apartment.postcode == osm_data.postcode,
            Apartment.country_code == country_code,
        )
        .first()
    )

    if existing:
        return existing, False

    # Create new apartment
    apartment = Apartment(
        osm_type=osm_data.osm_type,
        osm_id=osm_data.osm_id,
        osm_class=osm_data.osm_class,
        street=osm_data.street,
        house_number=osm_data.house_number,
        city=city,
        state=osm_data.state,
        postcode=osm_data.postcode,
        country=osm_data.country or "Unknown",
        country_code=country_code,
        display_name=osm_data.display_name,
    )

    try:
        db.add(apartment)
        db.commit()
        db.refresh(apartment)
        return apartment, True
    except IntegrityError:
        # Race condition: another request created the same apartment
        db.rollback()
        existing = (
            db.query(Apartment)
            .filter(
                Apartment.street == osm_data.street,
                Apartment.house_number == osm_data.house_number,
                Apartment.city == city,
                Apartment.postcode == osm_data.postcode,
                Apartment.country_code == country_code,
            )
            .first()
        )
        return existing, False


def get_apartment_by_id(db: Session, apartment_uid: UUID) -> Optional[Apartment]:
    """Get an apartment by its UID"""
    return db.query(Apartment).filter(Apartment.uid == apartment_uid).first()


def get_reviews_for_apartment(
    db: Session, apartment_uid: UUID, limit: int = 100
) -> list[Review]:
    """Get all reviews for a specific apartment"""
    return (
        db.query(Review)
        .filter(Review.apartment_uid == apartment_uid)
        .order_by(Review.created_at.desc())
        .limit(limit)
        .all()
    )


def get_user_review_for_apartment(
    db: Session, apartment_uid: UUID, user_uid: UUID
) -> Optional[Review]:
    """Check if a user has already reviewed a specific apartment"""
    return (
        db.query(Review)
        .filter(Review.apartment_uid == apartment_uid, Review.user_uid == user_uid)
        .first()
    )


class ReviewError(Enum):
    """Why a review could not be changed"""

    NOT_FOUND = "not_found"
    NOT_OWNER = "not_owner"


def get_own_review(
    db: Session, review_uid: UUID, user_uid: UUID
) -> Result[Review, ReviewError]:
    """Get a review, but only for the user who wrote it"""
    review = db.query(Review).filter(Review.uid == review_uid).first()
    if review is None:
        return Failure(ReviewError.NOT_FOUND)
    if review.user_uid != user_uid:
        return Failure(ReviewError.NOT_OWNER)
    return Success(review)


def update_own_review(
    db: Session, review_uid: UUID, user_uid: UUID, changes: ReviewUpdate
) -> Result[Review, ReviewError]:
    """Replace the text and ratings of a review; anything left out is cleared"""

    def save(review: Review) -> Review:
        for field, value in changes.model_dump().items():
            setattr(review, field, value)
        # An edited review has to be checked again before visitors see it
        review.status = "pending"
        review.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(review)
        return review

    return get_own_review(db, review_uid, user_uid).map(save)


def delete_own_review(
    db: Session, review_uid: UUID, user_uid: UUID
) -> Result[None, ReviewError]:
    """Delete a review for good, for the user who wrote it"""

    def remove(review: Review) -> None:
        db.delete(review)
        db.commit()

    return get_own_review(db, review_uid, user_uid).map(remove)


def calculate_apartment_average_rating(
    db: Session, apartment_uid: UUID
) -> Optional[float]:
    """Calculate the average rating for an apartment"""
    from sqlalchemy import func

    result = (
        db.query(func.avg(Review.rating))
        .filter(Review.apartment_uid == apartment_uid)
        .scalar()
    )

    return float(result) if result else None


def _overall_score(rating_averages: list) -> Optional[int]:
    """One 0–100 score from the per-rating averages; None if nobody rated anything."""
    given = [float(average) for average in rating_averages if average is not None]
    return round(sum(given) / len(given)) if given else None


@safe(exceptions=(SQLAlchemyError,))
def recently_reviewed_apartments(
    db: Session, limit: int, maps_api_key: Optional[str]
) -> list[RecentApartmentResponse]:
    """
    Apartments with a published review, most recently reviewed first.

    Counts, scores and the quoted text come from published reviews only.
    Returns Success(list), or Failure(error) when the database can't be read.
    """
    published = Review.status == "published"
    newest_review_text = (
        select(Review.content)
        .where(Review.apartment_uid == Apartment.uid, published)
        .order_by(Review.created_at.desc())
        .limit(1)
        .correlate(Apartment)
        .scalar_subquery()
    )
    rows = (
        db.query(
            Apartment,
            func.count(Review.uid),
            newest_review_text,
            func.avg(Review.landlord_rating),
            func.avg(Review.location_rating),
            func.avg(Review.condition_rating),
            func.avg(Review.quietness_rating),
        )
        .join(Review, Review.apartment_uid == Apartment.uid)
        .filter(published)
        .group_by(Apartment.uid)
        .order_by(func.max(Review.created_at).desc())
        .limit(limit)
        .all()
    )

    return [
        RecentApartmentResponse(
            uid=apartment.uid,
            house_number=apartment.house_number,
            street=apartment.street,
            city=apartment.city,
            state=apartment.state,
            postcode=apartment.postcode,
            display_name=apartment.display_name,
            review_count=review_count,
            average_score=_overall_score(averages),
            latest_review_text=latest_review_text,
            photo_url=street_view_photo_url(apartment.display_name, maps_api_key),
        )
        for apartment, review_count, latest_review_text, *averages in rows
    ]
