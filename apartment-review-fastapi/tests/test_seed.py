import pytest

from models import Apartment, Review, User
from seed import is_local_database, seed_database


def row_counts(db):
    return (
        db.query(User).count(),
        db.query(Apartment).count(),
        db.query(Review).count(),
    )


def test_the_sample_data_gives_the_home_page_four_cards_with_a_review_to_quote(
    client, db
):
    seed_database(db)

    apartments = client.get("/apartments/recent", params={"limit": 4}).json()

    assert len(apartments) == 4
    assert all(apartment["latest_review_text"] for apartment in apartments)


def test_the_sample_data_has_one_review_waiting_to_be_checked(db):
    seed_database(db)

    assert db.query(Review).filter(Review.status == "pending").count() == 1


def test_loading_the_sample_data_says_how_many_rows_it_added(db):
    seeded = seed_database(db).unwrap()

    assert (seeded.users, seeded.apartments, seeded.reviews) == row_counts(db)
    assert seeded.reviews > 0


def test_loading_the_sample_data_twice_adds_nothing_the_second_time(db):
    seed_database(db)
    after_first_run = row_counts(db)

    second = seed_database(db).unwrap()

    assert row_counts(db) == after_first_run
    assert (second.users, second.apartments, second.reviews) == (0, 0, 0)


@pytest.mark.parametrize(
    "database_url, is_local",
    [
        ("postgresql+psycopg://tom:123@localhost:5532/apartment_review", True),
        ("postgresql+psycopg://tom:123@127.0.0.1:5532/apartment_review", True),
        # the database's name inside Docker Compose
        ("postgresql+psycopg://tom:123@db:5432/apartment_review", True),
        ("sqlite:///:memory:", True),
        ("postgresql+psycopg://app:pw@ep-cool-sun-1234.aws.neon.tech/neondb", False),
        ("postgresql+psycopg://app:pw@db.example.com:5432/apartment_review", False),
    ],
)
def test_sample_data_is_only_for_a_database_on_this_machine(database_url, is_local):
    assert is_local_database(database_url) is is_local
