import logging
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from returns.result import Failure, Success

from config import google_maps_api_key
from controllers.apartments import get_or_create_apartment, recently_reviewed_apartments
from database import db_dependency
from models import Apartment
from schemas import (
    ApartmentCreate,
    ApartmentResponse,
    OSMAddressData,
    RecentApartmentResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter()


def get_maps_api_key() -> Optional[str]:
    return google_maps_api_key


@router.post("/apartment", response_model=ApartmentResponse)
async def create_apartment(apartment_data: ApartmentCreate, db: db_dependency):
    apartment = Apartment(**apartment_data.model_dump())
    db.add(apartment)
    db.commit()
    db.refresh(apartment)
    return apartment


@router.post(
    "/apartments/from-osm",
    response_model=ApartmentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def apartment_from_osm(osm_data: OSMAddressData, db: db_dependency):
    """The apartment at an address picked from the OpenStreetMap search; the first
    pick creates it."""
    apartment, _ = get_or_create_apartment(db, osm_data)
    return apartment


@router.get("/apartments/recent", response_model=list[RecentApartmentResponse])
async def recent_apartments(
    db: db_dependency,
    maps_api_key: Annotated[Optional[str], Depends(get_maps_api_key)],
    limit: Annotated[int, Query(ge=1, le=20)] = 10,
):
    """Recently reviewed apartments, for the home page."""
    match recently_reviewed_apartments(db, limit, maps_api_key):
        case Success(apartments):
            return apartments
        case Failure(error):
            logger.error("Could not list recently reviewed apartments", exc_info=error)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Reviews are unavailable right now",
            )
