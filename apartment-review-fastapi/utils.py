from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from models import Apartment, Review
from schemas import OSMAddressData
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
        latitude=osm_data.get_latitude(),
        longitude=osm_data.get_longitude(),
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


def get_apartments_by_location(
    db: Session,
    latitude: float,
    longitude: float,
    radius_km: float = 1.0,
    limit: int = 50,
) -> list[Apartment]:
    """
    Get apartments near a specific location.

    Note: This is a simple bounding box search. For production, consider using
    PostGIS for proper geographic queries.

    Args:
        db: Database session
        latitude: Center latitude
        longitude: Center longitude
        radius_km: Search radius in kilometers (approximate)
        limit: Maximum number of results

    Returns:
        List of apartments within the approximate radius
    """
    # Rough approximation: 1 degree ≈ 111 km
    lat_delta = radius_km / 111.0
    lon_delta = radius_km / (111.0 * abs(float(latitude)))

    apartments = (
        db.query(Apartment)
        .filter(
            Apartment.latitude.between(latitude - lat_delta, latitude + lat_delta),
            Apartment.longitude.between(longitude - lon_delta, longitude + lon_delta),
        )
        .limit(limit)
        .all()
    )

    return apartments


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
