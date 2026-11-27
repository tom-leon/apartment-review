from datetime import datetime
from enum import Enum
from returns.result import Failure, Result, Success
from sqlalchemy.orm import Session
from models import Review
from schemas import ReviewCreate, ReviewUpdate
from typing import Optional
from uuid import UUID
from controllers.apartments import get_apartment_by_id


def get_user_review_for_apartment(
    db: Session, apartment_uid: UUID, user_uid: UUID
) -> Optional[Review]:
    """Check if a user has already reviewed a specific apartment"""
    return (
        db.query(Review)
        .filter(Review.apartment_uid == apartment_uid, Review.user_uid == user_uid)
        .first()
    )


class ReviewError(Enum):
    """Why a review could not be read, saved or changed"""

    NOT_FOUND = "not_found"
    NOT_OWNER = "not_owner"
    NO_APARTMENT = "no_apartment"
    ALREADY_REVIEWED = "already_reviewed"


def create_review(
    db: Session, user_uid: UUID, review_data: ReviewCreate
) -> Result[Review, ReviewError]:
    """Save a new review, one per person per apartment; it starts as "pending" """
    if get_apartment_by_id(db, review_data.apartment_uid) is None:
        return Failure(ReviewError.NO_APARTMENT)
    if get_user_review_for_apartment(db, review_data.apartment_uid, user_uid):
        return Failure(ReviewError.ALREADY_REVIEWED)
    review = Review(user_uid=user_uid, **review_data.model_dump())
    db.add(review)
    db.commit()
    db.refresh(review)
    return Success(review)


def get_reviews_for_apartment(
    db: Session, apartment_uid: UUID, limit: int = 100
) -> Result[list[Review], ReviewError]:
    """The published reviews of an apartment, newest first"""
    if get_apartment_by_id(db, apartment_uid) is None:
        return Failure(ReviewError.NO_APARTMENT)
    return Success(
        db.query(Review)
        .filter(Review.apartment_uid == apartment_uid, Review.status == "published")
        .order_by(Review.created_at.desc())
        .limit(limit)
        .all()
    )


def get_own_review(
    db: Session, review_uid: UUID, user_uid: UUID
) -> Result[Review, ReviewError]:
    """Get a review, but only for the user who wrote it"""
    review = db.query(Review).filter(Review.uid == review_uid).first()
    if review is None:
        return Failure(ReviewError.NOT_FOUND)
    if review.user_uid != user_uid:
        return Failure(ReviewError.NOT_OWNER)
    return Success(review)


def update_own_review(
    db: Session, review_uid: UUID, user_uid: UUID, changes: ReviewUpdate
) -> Result[Review, ReviewError]:
    """Replace the text and ratings of a review; anything left out is cleared"""

    def save(review: Review) -> Review:
        for field, value in changes.model_dump().items():
            setattr(review, field, value)
        # An edited review has to be checked again before visitors see it
        review.status = "pending"
        review.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(review)
        return review

    return get_own_review(db, review_uid, user_uid).map(save)


def delete_own_review(
    db: Session, review_uid: UUID, user_uid: UUID
) -> Result[None, ReviewError]:
    """Delete a review for good, for the user who wrote it"""

    def remove(review: Review) -> None:
        db.delete(review)
        db.commit()

    return get_own_review(db, review_uid, user_uid).map(remove)
