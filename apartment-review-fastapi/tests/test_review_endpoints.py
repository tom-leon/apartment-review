from datetime import datetime

import pytest

from models import Apartment, Review, User
from test_auth import sign_in

NO_SUCH_UID = "00000000-0000-0000-0000-000000000000"


def add_user(db, name, google_sub):
    user = User(name=name, email=f"{name.lower()}@example.com", google_sub=google_sub)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def tenant(db):
    return add_user(db, "Tom", "google-1")


@pytest.fixture
def other_tenant(db):
    return add_user(db, "Mia", "google-2")


def signed_in(client, google_accounts, user):
    """The client, signed in as `user`."""
    sign_in(
        client,
        google_accounts,
        {"sub": user.google_sub, "email": user.email, "name": user.name},
    )
    return client


@pytest.fixture
def as_tenant(client, google_accounts, tenant):
    return signed_in(client, google_accounts, tenant)


@pytest.fixture
def as_other_tenant(client, google_accounts, other_tenant):
    return signed_in(client, google_accounts, other_tenant)


@pytest.fixture
def apartment(db):
    apartment = Apartment(
        city="Sydney",
        country="Australia",
        country_code="AU",
        display_name="1 Test St, Sydney, Australia",
    )
    db.add(apartment)
    db.commit()
    db.refresh(apartment)
    return apartment


def add_review(db, apartment, user, **fields):
    review = Review(apartment_uid=apartment.uid, user_uid=user.uid, **fields)
    db.add(review)
    db.commit()
    db.refresh(review)
    return review


@pytest.fixture
def review(db, apartment, tenant):
    """A published review written by `tenant`."""
    return add_review(
        db,
        apartment,
        tenant,
        content="Quiet street, slow repairs.",
        landlord_rating=40,
        location_rating=80,
        condition_rating=60,
        quietness_rating=90,
        status="published",
        created_at=datetime(2026, 1, 1),
        updated_at=datetime(2026, 1, 1),
    )


def post_review(client, apartment_uid, **fields):
    return client.post("/reviews", json={"apartment_uid": str(apartment_uid), **fields})


def test_signed_in_tenant_can_post_a_review(as_tenant, apartment, tenant, db):
    response = post_review(
        as_tenant,
        apartment.uid,
        content="Cold in winter, lovely neighbours.",
        landlord_rating=55,
        location_rating=90,
        condition_rating=35,
        quietness_rating=70,
    )

    assert response.status_code == 201
    review = db.query(Review).one()
    assert review.user_uid == tenant.uid
    assert review.apartment_uid == apartment.uid
    assert review.content == "Cold in winter, lovely neighbours."
    assert review.landlord_rating == 55
    assert review.quietness_rating == 70
    body = response.json()
    assert body["uid"] == str(review.uid)
    assert body["content"] == "Cold in winter, lovely neighbours."


def test_a_new_review_is_public_straight_away(as_tenant, apartment):
    post_review(as_tenant, apartment.uid, content="Fine.")

    visible = as_tenant.get(f"/apartments/{apartment.uid}/reviews").json()
    assert [each["content"] for each in visible] == ["Fine."]


def test_a_posted_review_does_not_say_who_wrote_it(as_tenant, apartment):
    response = post_review(as_tenant, apartment.uid, content="Fine.")

    assert "user_uid" not in response.json()


def test_the_unit_number_is_saved_with_the_review(as_tenant, apartment, db):
    post_review(as_tenant, apartment.uid, content="Fine.", unit_number="12A")

    assert db.query(Review).one().unit_number == "12A"


def test_the_unit_number_is_never_sent_back(as_tenant, apartment):
    posted = post_review(as_tenant, apartment.uid, content="Fine.", unit_number="12A")

    visible = as_tenant.get(f"/apartments/{apartment.uid}/reviews").json()
    assert "unit_number" not in posted.json()
    assert "unit_number" not in visible[0]


def test_an_edit_keeps_the_unit_number(as_tenant, apartment, db):
    posted = post_review(as_tenant, apartment.uid, content="Fine.", unit_number="12A")

    as_tenant.put(f"/reviews/{posted.json()['uid']}", json={"content": "Better."})

    assert db.query(Review).one().unit_number == "12A"


def test_posting_a_review_needs_sign_in(client, apartment, db):
    response = post_review(client, apartment.uid, content="Fine.")

    assert response.status_code == 401
    assert db.query(Review).count() == 0


def test_a_review_for_an_apartment_that_does_not_exist_is_refused(as_tenant, db):
    response = post_review(as_tenant, NO_SUCH_UID, content="Fine.")

    assert response.status_code == 404
    assert db.query(Review).count() == 0


def test_tenant_cannot_review_the_same_apartment_twice(as_tenant, review, db):
    response = post_review(as_tenant, review.apartment_uid, content="Again.")

    assert response.status_code == 409
    assert db.query(Review).count() == 1


def test_a_review_with_a_rating_above_100_is_refused(as_tenant, apartment, db):
    response = post_review(as_tenant, apartment.uid, landlord_rating=101)

    assert response.status_code == 422
    assert db.query(Review).count() == 0


def test_visitor_reads_the_published_reviews_newest_first(
    client, apartment, review, other_tenant, db
):
    add_review(
        db,
        apartment,
        other_tenant,
        content="New paint, same mould.",
        status="published",
        created_at=datetime(2026, 2, 1),
    )

    response = client.get(f"/apartments/{apartment.uid}/reviews")

    assert response.status_code == 200
    assert [each["content"] for each in response.json()] == [
        "New paint, same mould.",
        "Quiet street, slow repairs.",
    ]
    assert response.json()[1]["landlord_rating"] == 40


def test_visitor_does_not_see_a_review_that_is_not_published(
    client, apartment, review, other_tenant, db
):
    add_review(db, apartment, other_tenant, content="Held back.", status="pending")

    response = client.get(f"/apartments/{apartment.uid}/reviews")

    assert [each["content"] for each in response.json()] == [
        "Quiet street, slow repairs."
    ]


def test_reviews_a_visitor_reads_do_not_say_who_wrote_them(client, review):
    response = client.get(f"/apartments/{review.apartment_uid}/reviews")

    assert "user_uid" not in response.json()[0]


def test_reading_reviews_of_an_apartment_that_does_not_exist_fails(client):
    response = client.get(f"/apartments/{NO_SUCH_UID}/reviews")

    assert response.status_code == 404


def edit(client, review, body):
    return client.put(f"/reviews/{review.uid}", json=body)


def test_tenant_can_edit_their_own_review(as_tenant, review, db):
    response = edit(
        as_tenant,
        review,
        {
            "content": "Repairs got faster after the new agent took over.",
            "landlord_rating": 70,
            "location_rating": 85,
            "condition_rating": 65,
            "quietness_rating": 95,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["content"] == "Repairs got faster after the new agent took over."
    assert body["landlord_rating"] == 70
    assert body["location_rating"] == 85
    assert body["condition_rating"] == 65
    assert body["quietness_rating"] == 95
    db.refresh(review)
    assert review.content == "Repairs got faster after the new agent took over."
    assert review.landlord_rating == 70


def test_a_rating_left_out_of_an_edit_is_cleared(as_tenant, review, db):
    response = edit(as_tenant, review, {"content": "Only words now."})

    assert response.status_code == 200
    db.refresh(review)
    assert review.content == "Only words now."
    assert review.landlord_rating is None
    assert review.quietness_rating is None


def test_an_edit_with_a_rating_above_100_is_refused(as_tenant, review, db):
    response = edit(as_tenant, review, {"content": "Great.", "landlord_rating": 101})

    assert response.status_code == 422
    db.refresh(review)
    assert review.content == "Quiet street, slow repairs."
    assert review.landlord_rating == 40


def test_an_edited_review_stays_public(as_tenant, review):
    edit(as_tenant, review, {"content": "Rewritten after publishing."})

    visible = as_tenant.get(f"/apartments/{review.apartment_uid}/reviews").json()
    assert [each["content"] for each in visible] == ["Rewritten after publishing."]


def test_an_edit_records_when_the_review_changed(as_tenant, review, db):
    edit(as_tenant, review, {"content": "Rewritten after publishing."})

    db.refresh(review)
    assert review.updated_at > datetime(2026, 1, 1)
    assert review.created_at == datetime(2026, 1, 1)


def test_tenant_cannot_edit_someone_elses_review(as_other_tenant, review, db):
    response = edit(as_other_tenant, review, {"content": "Hijacked."})

    assert response.status_code == 403
    db.refresh(review)
    assert review.content == "Quiet street, slow repairs."
    assert review.status == "published"


def test_editing_a_review_that_does_not_exist_fails(as_tenant):
    response = as_tenant.put(
        f"/reviews/{NO_SUCH_UID}", json={"content": "Nothing to edit."}
    )

    assert response.status_code == 404


def test_tenant_can_delete_their_own_review(as_tenant, review, db):
    response = as_tenant.delete(f"/reviews/{review.uid}")

    assert response.status_code == 204
    assert db.query(Review).count() == 0


def test_tenant_cannot_delete_someone_elses_review(as_other_tenant, review, db):
    response = as_other_tenant.delete(f"/reviews/{review.uid}")

    assert response.status_code == 403
    assert db.query(Review).count() == 1


def test_deleting_a_review_that_does_not_exist_fails(as_tenant):
    response = as_tenant.delete(f"/reviews/{NO_SUCH_UID}")

    assert response.status_code == 404


def test_editing_a_review_needs_sign_in(client, review, db):
    response = edit(client, review, {"content": "Hijacked."})

    assert response.status_code == 401
    db.refresh(review)
    assert review.content == "Quiet street, slow repairs."


def test_deleting_a_review_needs_sign_in(client, review, db):
    response = client.delete(f"/reviews/{review.uid}")

    assert response.status_code == 401
    assert db.query(Review).count() == 1
