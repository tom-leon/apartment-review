from datetime import datetime

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

import example_endpoints
from models import Apartment, Review, User


@pytest.fixture
def review_client(testing_session):
    """A client for the drafted review routes, which main.py does not load yet."""
    app = FastAPI()
    app.include_router(example_endpoints.router)

    def override_get_db():
        db = testing_session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[example_endpoints.get_db] = override_get_db
    return TestClient(app)


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


@pytest.fixture
def review(db, tenant):
    """A published review written by `tenant`."""
    apartment = Apartment(
        city="Sydney",
        country="Australia",
        country_code="AU",
        display_name="1 Test St, Sydney, Australia",
    )
    db.add(apartment)
    db.commit()
    review = Review(
        apartment_uid=apartment.uid,
        user_uid=tenant.uid,
        content="Quiet street, slow repairs.",
        landlord_rating=40,
        location_rating=80,
        condition_rating=60,
        quietness_rating=90,
        status="published",
        created_at=datetime(2026, 1, 1),
        updated_at=datetime(2026, 1, 1),
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    return review


def edit(review_client, review, user, body):
    return review_client.put(
        f"/reviews/{review.uid}", params={"user_uid": str(user.uid)}, json=body
    )


def test_tenant_can_edit_their_own_review(review_client, review, tenant, db):
    response = edit(
        review_client,
        review,
        tenant,
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


def test_a_rating_left_out_of_an_edit_is_cleared(review_client, review, tenant, db):
    response = edit(review_client, review, tenant, {"content": "Only words now."})

    assert response.status_code == 200
    db.refresh(review)
    assert review.content == "Only words now."
    assert review.landlord_rating is None
    assert review.quietness_rating is None


def test_edit_rejects_a_rating_above_100(review_client, review, tenant, db):
    response = edit(
        review_client, review, tenant, {"content": "Great.", "landlord_rating": 101}
    )

    assert response.status_code == 422
    db.refresh(review)
    assert review.content == "Quiet street, slow repairs."
    assert review.landlord_rating == 40


def test_an_edited_review_goes_back_to_pending(review_client, review, tenant, db):
    edit(review_client, review, tenant, {"content": "Rewritten after publishing."})

    db.refresh(review)
    assert review.status == "pending"


def test_an_edit_records_when_the_review_changed(review_client, review, tenant, db):
    edit(review_client, review, tenant, {"content": "Rewritten after publishing."})

    db.refresh(review)
    assert review.updated_at > datetime(2026, 1, 1)
    assert review.created_at == datetime(2026, 1, 1)


def test_tenant_cannot_edit_someone_elses_review(
    review_client, review, other_tenant, db
):
    response = edit(review_client, review, other_tenant, {"content": "Hijacked."})

    assert response.status_code == 403
    db.refresh(review)
    assert review.content == "Quiet street, slow repairs."
    assert review.status == "published"


def test_editing_an_unknown_review_returns_404(review_client, tenant):
    response = review_client.put(
        "/reviews/00000000-0000-0000-0000-000000000000",
        params={"user_uid": str(tenant.uid)},
        json={"content": "Nothing to edit."},
    )

    assert response.status_code == 404


def test_tenant_can_delete_their_own_review(review_client, review, tenant, db):
    response = review_client.delete(
        f"/reviews/{review.uid}", params={"user_uid": str(tenant.uid)}
    )

    assert response.status_code == 204
    assert db.query(Review).count() == 0


def test_tenant_cannot_delete_someone_elses_review(
    review_client, review, other_tenant, db
):
    response = review_client.delete(
        f"/reviews/{review.uid}", params={"user_uid": str(other_tenant.uid)}
    )

    assert response.status_code == 403
    assert db.query(Review).count() == 1


def test_deleting_an_unknown_review_returns_404(review_client, tenant):
    response = review_client.delete(
        "/reviews/00000000-0000-0000-0000-000000000000",
        params={"user_uid": str(tenant.uid)},
    )

    assert response.status_code == 404
