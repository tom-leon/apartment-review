import logging

from fastapi import FastAPI, Depends, HTTPException, Query, Request, status
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from returns.result import Failure, Success
from typing import Annotated, Optional
from uuid import UUID
from models import Apartment, User
from schemas import (
    ApartmentCreate,
    ApartmentResponse,
    RecentApartmentResponse,
    UserResponse,
)
from config import cors_origins, google_maps_api_key, session_https_only, session_secret
from database import engine, SessionLocal
from sqlalchemy.orm import Session
from sqlmodel import SQLModel
from utils import recently_reviewed_apartments
from auth import find_or_create_user, verify_google_token

logger = logging.getLogger(__name__)

app = FastAPI()

# Before CORS so CORS stays outermost: the last middleware added wraps all the rest.
app.add_middleware(
    SessionMiddleware,
    secret_key=session_secret,
    https_only=session_https_only,
    same_site="lax",
)
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


def current_user(request: Request, db: db_dependency) -> User:
    """The signed-in user, from the session cookie; 401 when there is none."""
    user_uid = request.session.get("user_uid")
    user = db.get(User, UUID(user_uid)) if user_uid else None
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Sign in first"
        )
    return user


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


@app.post("/auth/google", response_model=UserResponse)
async def google_sign_in(
    request: Request,
    db: db_dependency,
    claims: Annotated[dict, Depends(verify_google_token)],
):
    """Sign in with the ID token from Google's button; first time creates the user."""
    match find_or_create_user(db, claims):
        case Success(user):
            request.session["user_uid"] = str(user.uid)
            return user
        case Failure(error):
            logger.error("Could not sign in", exc_info=error)
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Sign-in is unavailable right now",
            )


@app.get("/auth/me", response_model=UserResponse)
async def me(user: Annotated[User, Depends(current_user)]):
    """The signed-in user, or 401."""
    return user


@app.post("/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(request: Request):
    """End the session; the browser forgets the cookie."""
    request.session.clear()


@app.get("/")
async def health_check():
    """Health check endpoint to verify the API is running."""
    return {"status": "healthy", "message": "API is running"}
