import logging
from typing import Annotated, Optional

from fastapi import Depends, HTTPException, status
from google.auth.exceptions import GoogleAuthError
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from returns.result import Failure, Success, safe
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from config import google_client_id
from models import User
from schemas import GoogleCredential

logger = logging.getLogger(__name__)


def get_google_client_id() -> Optional[str]:
    return google_client_id


@safe(exceptions=(ValueError, GoogleAuthError))
def _google_claims(credential: str, client_id: str) -> dict:
    """What Google says about the account behind an ID token, if the token is good."""
    return id_token.verify_oauth2_token(
        credential, google_requests.Request(), client_id
    )


def verify_google_token(
    body: GoogleCredential,
    client_id: Annotated[Optional[str], Depends(get_google_client_id)],
) -> dict:
    """The claims in the ID token the frontend sends; 401 when Google rejects it."""
    if client_id is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google sign-in is not configured",
        )
    match _google_claims(body.credential, client_id):
        case Success(claims):
            return claims
        case Failure(error):
            logger.warning("Google rejected a sign-in", exc_info=error)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not verify the Google sign-in",
            )


@safe(exceptions=(SQLAlchemyError,))
def find_or_create_user(db: Session, claims: dict) -> User:
    """The user behind a Google account, created on first sign-in.

    Returns Success(user), or Failure(error) when the database can't be used."""
    user = db.query(User).filter(User.google_sub == claims["sub"]).first()
    if user is None:
        user = User(
            google_sub=claims["sub"],
            email=claims["email"],
            name=claims.get("name") or claims["email"],
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user
