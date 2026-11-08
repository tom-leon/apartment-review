from fastapi import FastAPI, Depends
from typing import Annotated
from models import User, Apartment
from schemas import UserCreate, UserResponse, ApartmentCreate, ApartmentResponse
from database import engine, SessionLocal
from sqlalchemy.orm import Session
from sqlmodel import SQLModel

app = FastAPI()


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


@app.post("/user", response_model=UserResponse)
async def create_user(user_data: UserCreate, db: db_dependency):
    user = User(**user_data.model_dump())
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


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
