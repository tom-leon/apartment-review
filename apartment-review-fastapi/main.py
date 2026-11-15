from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import Annotated
from models import Apartment
from schemas import ApartmentCreate, ApartmentResponse
from config import cors_origins
from database import engine, SessionLocal
from sqlalchemy.orm import Session
from sqlmodel import SQLModel

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


@app.post("/apartment", response_model=ApartmentResponse)
async def create_apartment(apartment_data: ApartmentCreate, db: db_dependency):
    apartment = Apartment(**apartment_data.model_dump())
    db.add(apartment)
    db.commit()
    db.refresh(apartment)
    return apartment


@app.get("/")
async def health_check():
    """Health check endpoint to verify the API is running."""
    return {"status": "healthy", "message": "API is running"}
