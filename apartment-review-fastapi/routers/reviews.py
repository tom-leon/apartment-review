from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from returns.result import Failure, Success

from controllers.auth import current_user
from database import db_dependency
from models import User
from schemas import ReviewCreate, ReviewResponse, ReviewUpdate
from controllers.reviews import (
    ReviewError,
    create_review,
    delete_own_review,
    get_reviews_for_apartment,
    update_own_review,
)

router = APIRouter()

signed_in_user = Annotated[User, Depends(current_user)]

HTTP_ERRORS = {
    ReviewError.NOT_FOUND: (status.HTTP_404_NOT_FOUND, "Review not found"),
    ReviewError.NOT_OWNER: (
        status.HTTP_403_FORBIDDEN,
        "You can only change your own review",
    ),
    ReviewError.NO_APARTMENT: (status.HTTP_404_NOT_FOUND, "Apartment not found"),
    ReviewError.ALREADY_REVIEWED: (
        status.HTTP_409_CONFLICT,
        "You have already reviewed this apartment",
    ),
}


def review_http_error(error: ReviewError) -> HTTPException:
    """The HTTP error for a review that could not be read, saved or changed"""
    status_code, detail = HTTP_ERRORS[error]
    return HTTPException(status_code=status_code, detail=detail)


@router.post(
    "/reviews", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED
)
async def post_review(
    review_data: ReviewCreate, user: signed_in_user, db: db_dependency
):
    """Post your review of an apartment. Visitors see it straight away."""
    match create_review(db, user.uid, review_data):
        case Success(review):
            return review
        case Failure(error):
            raise review_http_error(error)


@router.get("/apartments/{apartment_uid}/reviews", response_model=list[ReviewResponse])
async def apartment_reviews(apartment_uid: UUID, db: db_dependency):
    """The published reviews of an apartment, newest first"""
    match get_reviews_for_apartment(db, apartment_uid):
        case Success(reviews):
            return reviews
        case Failure(error):
            raise review_http_error(error)


@router.put("/reviews/{review_uid}", response_model=ReviewResponse)
async def update_review(
    review_uid: UUID,
    review_data: ReviewUpdate,
    user: signed_in_user,
    db: db_dependency,
):
    """Replace the text and ratings of your own review; anything left out is cleared."""
    match update_own_review(db, review_uid, user.uid, review_data):
        case Success(review):
            return review
        case Failure(error):
            raise review_http_error(error)


@router.delete("/reviews/{review_uid}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_review(review_uid: UUID, user: signed_in_user, db: db_dependency):
    """Delete your own review for good"""
    match delete_own_review(db, review_uid, user.uid):
        case Failure(error):
            raise review_http_error(error)
