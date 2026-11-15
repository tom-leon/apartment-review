import logging

from fastapi import FastAPI, Depends, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from returns.result import Failure, Success
from typing import Annotated, Optional
from models import Apartment
from schemas import ApartmentCreate, ApartmentResponse, RecentApartmentResponse
from config import cors_origins, google_maps_api_key
from database import engine, SessionLocal
from sqlalchemy.orm import Session
from sqlmodel import SQLModel
from utils import recently_reviewed_apartments

logger = logging.getLogger(__name__)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def create_tables():
    SQLModel.metadata.create_all(engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]


def get_maps_api_key() -> Optional[str]:
    return google_maps_api_key


@app.post("/apartment", response_model=ApartmentResponse)
async def create_apartment(apartment_data: ApartmentCreate, db: db_dependency):
    apartment = Apartment(**apartment_data.model_dump())
    db.add(apartment)
    db.commit()
    db.refresh(apartment)
    return apartment


@app.get("/apartments/recent", response_model=list[RecentApartmentResponse])
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


@app.get("/")
async def health_check():
    """Health check endpoint to verify the API is running."""
    return {"status": "healthy", "message": "API is running"}
