from controllers import auth
import main
from models import User

TOM = {"sub": "123", "email": "tom@example.com", "name": "Tom Leon"}


def sign_in(client, google_accounts, claims=TOM):
    """Sign in through the stand-in Google as the account the claims describe."""
    google_accounts["tom-token"] = claims
    return client.post("/auth/google", json={"credential": "tom-token"})


def test_signing_in_with_google_the_first_time_makes_a_new_user(
    client, db, google_accounts
):
    response = sign_in(client, google_accounts)

    assert response.status_code == 200
    user = db.query(User).one()
    assert user.google_sub == "123"
    body = response.json()
    assert body["uid"] == str(user.uid)
    assert body["name"] == "Tom Leon"
    assert body["email"] == "tom@example.com"
    assert "google_sub" not in body


def test_sign_in_fails_when_the_proof_from_google_is_missing(client):
    assert client.post("/auth/google", json={}).status_code == 422


def test_sign_in_fails_when_google_says_the_proof_is_fake(client, db, google_accounts):
    response = client.post("/auth/google", json={"credential": "garbage"})

    assert response.status_code == 401
    assert db.query(User).count() == 0
    assert "set-cookie" not in response.headers


def test_sign_in_says_try_later_when_google_sign_in_is_not_set_up(client):
    # The real verifier runs here; with no client ID it must stop before asking Google.
    main.app.dependency_overrides[auth.get_google_client_id] = lambda: None

    response = client.post("/auth/google", json={"credential": "anything"})

    assert response.status_code == 503
    assert response.json() == {"detail": "Google sign-in is not configured"}


def test_signing_in_again_with_the_same_google_account_does_not_make_a_second_user(
    client, db, google_accounts
):
    first = sign_in(client, google_accounts)
    second = sign_in(
        client, google_accounts, {**TOM, "name": "Tom L", "email": "tom@new.example"}
    )

    assert second.json()["uid"] == first.json()["uid"]
    assert db.query(User).count() == 1
    # What Google sends on a later sign-in is not copied over the stored user.
    assert second.json()["name"] == "Tom Leon"


def test_the_email_is_used_as_the_name_when_google_gives_no_name(
    client, google_accounts
):
    response = sign_in(
        client, google_accounts, {"sub": "123", "email": "tom@example.com"}
    )

    assert response.status_code == 200
    assert response.json()["name"] == "tom@example.com"


def test_sign_in_says_try_later_when_the_database_is_broken(
    client, db, google_accounts, caplog
):
    # No user table any more, so the query fails for real.
    User.__table__.drop(db.get_bind())

    response = sign_in(client, google_accounts)

    assert response.status_code == 503
    assert "no such table" in caplog.text


def test_the_sign_in_is_remembered_and_hidden_from_scripts_on_the_page(
    client, google_accounts
):
    response = sign_in(client, google_accounts)

    cookie = response.headers["set-cookie"]
    flags = [part.strip().lower() for part in cookie.split(";")[1:]]
    assert cookie.startswith("session=")
    assert "httponly" in flags
    assert "samesite=lax" in flags
    # Tests run over http; production turns Secure on with SESSION_HTTPS_ONLY=true.
    assert "secure" not in flags


def test_the_app_can_tell_who_is_signed_in(client, google_accounts):
    signed_in = sign_in(client, google_accounts)

    response = client.get("/auth/me")

    assert response.status_code == 200
    assert response.json() == signed_in.json()


def test_the_app_says_so_when_nobody_is_signed_in(client):
    assert client.get("/auth/me").status_code == 401


def test_a_fake_sign_in_is_not_believed(client):
    # Not signed by the server, so Starlette treats it as no session at all.
    client.cookies.set("session", "garbage")

    assert client.get("/auth/me").status_code == 401


def test_a_deleted_user_is_no_longer_signed_in(client, db, google_accounts):
    sign_in(client, google_accounts)
    db.delete(db.query(User).one())
    db.commit()

    assert client.get("/auth/me").status_code == 401


def test_after_signing_out_you_are_no_longer_signed_in(client, google_accounts):
    sign_in(client, google_accounts)

    response = client.post("/auth/logout")

    assert response.status_code == 204
    assert client.get("/auth/me").status_code == 401
