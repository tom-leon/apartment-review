import pytest
from sqlalchemy.exc import IntegrityError

from models import User


def test_user_is_found_by_google_id(db):
    db.add(User(name="Tom", email="tom@example.com", google_sub="1001"))
    db.commit()

    found = db.query(User).filter(User.google_sub == "1001").one()

    assert found.email == "tom@example.com"


def test_two_users_cannot_share_a_google_id(db):
    db.add(User(name="Tom", email="tom@example.com", google_sub="1001"))
    db.commit()
    db.add(User(name="Thomas", email="thomas@example.com", google_sub="1001"))

    with pytest.raises(IntegrityError, match="google_sub"):
        db.commit()


def test_two_google_accounts_can_have_the_same_email(db):
    db.add(User(name="Tom", email="tom@example.com", google_sub="1001"))
    db.commit()
    db.add(User(name="Thomas", email="tom@example.com", google_sub="1002"))
    db.commit()

    assert db.query(User).filter(User.email == "tom@example.com").count() == 2
