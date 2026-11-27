"""
Sample data for a local database: made-up apartments, reviewers and reviews, so the
pages have something to show before anyone can sign in and post.

Run from this folder:

    uv run python seed.py

It only writes to a database on this machine, and running it again adds nothing.
"""

import sys
from dataclasses import dataclass
from datetime import datetime

from returns.result import Failure, Success, safe
from sqlalchemy.engine import make_url
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from config import database_url
from database import SessionLocal
from models import Apartment, Review, User

# No Google account has an ID like this, so nobody can sign in as a sample reviewer.
_SAMPLE_GOOGLE_SUB = "seed-"
_SAMPLE_REVIEWERS = 5
_LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1", "db"}  # "db" = Docker Compose

# Street names are made up on purpose: an invented review must never sit on a real
# address. house number, street, suburb, city, state, postcode
_APARTMENTS = [
    ("12", "Sample Street", "Fitzroy", "Melbourne", "Victoria", "3065"),
    ("88", "Example Road", "Glebe", "Sydney", "New South Wales", "2037"),
    ("15", "Demo Avenue", "West End", "Brisbane", "Queensland", "4101"),
    ("7", "Placeholder Parade", "Adelaide", "Adelaide", "South Australia", "5000"),
    ("301", "Mock Lane", "Perth", "Perth", "Western Australia", "6000"),
    ("9", "Testing Terrace", "Hobart", "Hobart", "Tasmania", "7000"),
]

# apartment (position above), reviewer, written on, status,
# (landlord, location, condition, quietness), text
_REVIEWS = [
    (
        0,
        0,
        datetime(2026, 8, 2),
        "published",
        (60, 95, 70, 35),
        "Trams run past the bedroom window until 1am. Pick a unit at the back.",
    ),
    (
        0,
        1,
        datetime(2026, 9, 14),
        "published",
        (70, 90, 80, 60),
        "Solid old building with thick walls. A leaking tap was fixed within the week.",
    ),
    (
        0,
        2,
        datetime(2026, 11, 10),
        "published",
        (55, 95, 75, 79),
        "Great light and a short walk to everything, but repairs took six weeks.",
    ),
    (
        1,
        0,
        datetime(2026, 11, 8),
        "published",
        (88, 92, 70, 90),
        "Quiet street, five minutes to the light rail, and every email was answered "
        "within a day. The one real problem is damp in the back bedroom each winter, "
        "which gets painted over instead of fixed. Ask to see that room with the "
        "wardrobe pulled away from the wall before you sign anything.",
    ),
    (
        2,
        1,
        datetime(2026, 10, 1),
        "published",
        (50, 80, 40, 10),
        "The bar downstairs plays music until 3am on weekends.",
    ),
    (
        2,
        3,
        datetime(2026, 11, 5),
        "published",
        (20, 75, 30, 23),
        "Cockroaches in the kitchen, and the lift was out for a month.",
    ),
    # No ratings at all: shows a card without a score
    (
        3,
        4,
        datetime(2026, 11, 1),
        "published",
        (None, None, None, None),
        "Bond came back in full within a week. No dramas.",
    ),
    # Fifth most recent: shows that the home page stops at four cards
    (
        4,
        2,
        datetime(2026, 6, 1),
        "published",
        (90, 85, 88, 80),
        "Quiet, clean, and the heating actually works.",
    ),
    (
        4,
        3,
        datetime(2026, 7, 20),
        "published",
        (75, 85, 80, 70),
        "Fair rent for the area. Parking is a fight after 6pm.",
    ),
    # Still waiting to be checked: visitors must not see this one
    (
        5,
        4,
        datetime(2026, 11, 15),
        "pending",
        (30, 60, 20, 50),
        "Mould on the bathroom ceiling came back after every repaint.",
    ),
]


@dataclass
class Seeded:
    """How many rows one run added."""

    users: int = 0
    apartments: int = 0
    reviews: int = 0


def is_local_database(database_url: str) -> bool:
    """True for SQLite and for Postgres on this machine or in Docker Compose."""
    url = make_url(database_url)
    return url.drivername.startswith("sqlite") or url.host in _LOCAL_HOSTS


@safe(exceptions=(SQLAlchemyError,))
def seed_database(db: Session) -> Seeded:
    """
    Add the sample reviewers, apartments and reviews, unless they are already there.

    Returns Success(Seeded), or Failure(error) when the database can't be written.
    """
    already_seeded = (
        db.query(User).filter(User.google_sub.startswith(_SAMPLE_GOOGLE_SUB)).first()
    )
    if already_seeded:
        return Seeded()

    reviewers = [
        User(
            name=f"Sample Reviewer {number}",
            email=f"sample.reviewer{number}@example.com",
            google_sub=f"{_SAMPLE_GOOGLE_SUB}{number}",
        )
        for number in range(1, _SAMPLE_REVIEWERS + 1)
    ]
    apartments = [
        Apartment(
            house_number=house_number,
            street=street,
            city=city,
            state=state,
            postcode=postcode,
            country="Australia",
            country_code="AU",
            display_name=(
                f"{house_number}, {street}, {suburb}, {city}, {state}, {postcode}, "
                "Australia"
            ),
        )
        for house_number, street, suburb, city, state, postcode in _APARTMENTS
    ]
    reviews = [
        Review(
            apartment_uid=apartments[apartment].uid,
            user_uid=reviewers[reviewer].uid,
            created_at=written_on,
            status=status,
            content=text,
            landlord_rating=landlord,
            location_rating=location,
            condition_rating=condition,
            quietness_rating=quietness,
        )
        for (
            apartment,
            reviewer,
            written_on,
            status,
            (landlord, location, condition, quietness),
            text,
        ) in _REVIEWS
    ]

    db.add_all(reviewers + apartments)
    db.flush()  # reviewers and apartments first: reviews point at them
    db.add_all(reviews)
    db.commit()
    return Seeded(
        users=len(reviewers), apartments=len(apartments), reviews=len(reviews)
    )


def main() -> int:
    if not is_local_database(database_url):
        print("Not adding sample data: DATABASE_URL is not a database on this machine.")
        return 1

    with SessionLocal() as db:
        match seed_database(db):
            case Success(Seeded(users=0, apartments=0, reviews=0)):
                print("Sample data is already there. Nothing added.")
                return 0
            case Success(seeded):
                print(
                    f"Added {seeded.users} sample reviewers, {seeded.apartments} "
                    f"apartments and {seeded.reviews} reviews."
                )
                return 0
            case Failure(error):
                print(f"Could not add sample data: {error}")
                return 1


if __name__ == "__main__":
    sys.exit(main())
