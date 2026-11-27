import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, status
from returns.result import Failure, Success

from controllers.auth import current_user, find_or_create_user, verify_google_token
from database import db_dependency
from models import User
from schemas import UserResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/auth/google", response_model=UserResponse)
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


@router.get("/auth/me", response_model=UserResponse)
async def me(user: Annotated[User, Depends(current_user)]):
    """The signed-in user, or 401."""
    return user


@router.post("/auth/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(request: Request):
    """End the session; the browser forgets the cookie."""
    request.session.clear()
