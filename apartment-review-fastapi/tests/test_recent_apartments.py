from datetime import datetime
from itertools import count
from urllib.parse import parse_qs, urlsplit

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import main
from routers import apartments
from models import Apartment, Review, User

_reviewer_number = count(1)


@pytest.fixture(autouse=True)
def maps_key(client):
    """No Google Maps key unless a test sets one, whatever the machine's environment."""

    def use(api_key):
        main.app.dependency_overrides[apartments.get_maps_api_key] = lambda: api_key

    use(None)
    return use


def add_apartment(db, house_number, street, city="Melbourne", postcode="3065"):
    apartment = Apartment(
        house_number=house_number,
        street=street,
        city=city,
        state="Victoria",
        postcode=postcode,
        country="Australia",
        country_code="AU",
        display_name=f"{house_number} {street}, {city} {postcode}",
    )
    db.add(apartment)
    db.commit()
    db.refresh(apartment)
    return apartment


def add_review(db, apartment, written_at=datetime(2026, 1, 1), **fields):
    # One review per person per apartment, so every review gets its own reviewer.
    number = next(_reviewer_number)
    reviewer = User(
        name=f"Reviewer {number}",
        email=f"reviewer{number}@example.com",
        google_sub=f"google-{number}",
    )
    db.add(reviewer)
    db.commit()
    review = Review(
        apartment_uid=apartment.uid,
        user_uid=reviewer.uid,
        created_at=written_at,
        **fields,
    )
    db.add(review)
    db.commit()
    return review


def test_recent_is_empty_when_nothing_has_been_reviewed(client, db):
    add_apartment(db, "1", "Empty Street")

    response = client.get("/apartments/recent")

    assert response.status_code == 200
    assert response.json() == []


def test_recent_describes_a_reviewed_apartment_without_saying_who_reviewed_it(
    client, db
):
    apartment = add_apartment(db, "12", "Brunswick Street")
    add_review(
        db,
        apartment,
        status="published",
        content="Great light, but repairs took six weeks.",
        landlord_rating=40,
        location_rating=90,
        condition_rating=70,
        quietness_rating=80,
    )

    response = client.get("/apartments/recent")

    assert response.status_code == 200
    assert response.json() == [
        {
            "uid": str(apartment.uid),
            "house_number": "12",
            "street": "Brunswick Street",
            "city": "Melbourne",
            "state": "Victoria",
            "postcode": "3065",
            "display_name": "12 Brunswick Street, Melbourne 3065",
            "review_count": 1,
            "average_score": 70,
            "latest_review_text": "Great light, but repairs took six weeks.",
            "photo_url": None,
        }
    ]


def all_ratings(score):
    return {
        "landlord_rating": score,
        "location_rating": score,
        "condition_rating": score,
        "quietness_rating": score,
    }


def test_recent_shows_only_published_reviews(client, db):
    checked = add_apartment(db, "12", "Brunswick Street")
    add_review(
        db,
        checked,
        written_at=datetime(2026, 1, 1),
        status="published",
        content="Published words",
        **all_ratings(80),
    )
    add_review(
        db,
        checked,
        written_at=datetime(2026, 2, 1),
        status="pending",
        content="Pending words",
        **all_ratings(0),
    )
    add_review(
        db,
        checked,
        written_at=datetime(2026, 3, 1),
        status="rejected",
        content="Rejected words",
        **all_ratings(0),
    )
    unchecked = add_apartment(db, "88", "Glebe Point Road", "Sydney", "2037")
    add_review(db, unchecked, status="pending", content="Not checked yet")

    apartments = client.get("/apartments/recent").json()

    assert [apartment["street"] for apartment in apartments] == ["Brunswick Street"]
    assert apartments[0]["review_count"] == 1
    assert apartments[0]["average_score"] == 80
    assert apartments[0]["latest_review_text"] == "Published words"


def test_a_new_review_is_published(db):
    apartment = add_apartment(db, "12", "Brunswick Street")

    review = add_review(db, apartment, content="Fresh from the form")

    db.refresh(review)
    assert review.status == "published"


def test_recent_quotes_the_newest_published_review(client, db):
    apartment = add_apartment(db, "12", "Brunswick Street")
    add_review(
        db,
        apartment,
        written_at=datetime(2026, 1, 1),
        status="published",
        content="Zebra crossing outside beeps all night",
    )
    add_review(
        db,
        apartment,
        written_at=datetime(2026, 2, 1),
        status="published",
        content="A quiet block now the crossing is gone",
    )

    apartments = client.get("/apartments/recent").json()

    assert apartments[0]["latest_review_text"] == (
        "A quiet block now the crossing is gone"
    )


def test_recent_puts_the_newest_review_first_and_stops_at_the_limit(client, db):
    january = add_apartment(db, "1", "January Street")
    march = add_apartment(db, "3", "March Street")
    february = add_apartment(db, "2", "February Street")
    add_review(db, january, written_at=datetime(2026, 1, 15), status="published")
    add_review(db, march, written_at=datetime(2026, 3, 15), status="published")
    add_review(db, february, written_at=datetime(2026, 2, 15), status="published")

    apartments = client.get("/apartments/recent", params={"limit": 2}).json()

    assert [apartment["street"] for apartment in apartments] == [
        "March Street",
        "February Street",
    ]


def test_recent_score_averages_the_ratings_and_skips_the_ones_nobody_gave(client, db):
    apartment = add_apartment(db, "12", "Brunswick Street")
    add_review(
        db, apartment, status="published", landlord_rating=100, location_rating=40
    )
    add_review(
        db, apartment, status="published", landlord_rating=60, location_rating=40
    )

    apartments = client.get("/apartments/recent").json()

    # landlord averages 80, location averages 40, nobody rated the other two
    assert apartments[0]["average_score"] == 60


def test_recent_has_no_score_when_no_review_gave_a_rating(client, db):
    apartment = add_apartment(db, "12", "Brunswick Street")
    add_review(db, apartment, status="published", content="Words only")

    apartments = client.get("/apartments/recent").json()

    assert apartments[0]["average_score"] is None


def test_recent_gives_a_street_photo_address_when_a_maps_key_is_set(
    client, db, maps_key
):
    maps_key("test-key")
    apartment = add_apartment(db, "12", "Brunswick Street")
    add_review(db, apartment, status="published")

    apartments = client.get("/apartments/recent").json()

    photo = urlsplit(apartments[0]["photo_url"])
    assert photo.netloc == "maps.googleapis.com"
    assert parse_qs(photo.query)["location"] == ["12 Brunswick Street, Melbourne 3065"]
    assert parse_qs(photo.query)["key"] == ["test-key"]


def test_recent_says_try_later_when_the_database_is_broken(client, caplog):
    # A real database with no tables in it, so the query fails for real.
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    broken_session = sessionmaker(bind=engine)

    def broken_db():
        db = broken_session()
        try:
            yield db
        finally:
            db.close()

    main.app.dependency_overrides[main.get_db] = broken_db

    response = client.get("/apartments/recent")

    assert response.status_code == 503
    assert "no such table" in caplog.text
