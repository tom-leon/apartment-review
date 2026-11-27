import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from config import cors_origins, session_https_only, session_secret
from database import engine, get_db  # noqa: F401 (tests swap get_db)
from sqlmodel import SQLModel
from routers import apartments, auth, reviews

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


app.include_router(apartments.router)
app.include_router(auth.router)
app.include_router(reviews.router)


@app.get("/")
async def health_check():
    """Health check endpoint to verify the API is running."""
    return {"status": "healthy", "message": "API is running"}
