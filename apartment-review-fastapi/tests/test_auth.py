import auth
import main
from models import User

TOM = {"sub": "123", "email": "tom@example.com", "name": "Tom Leon"}


def sign_in(client, google_accounts, claims=TOM):
    """Sign in through the stand-in Google as the account the claims describe."""
    google_accounts["tom-token"] = claims
    return client.post("/auth/google", json={"credential": "tom-token"})


def test_google_sign_in_creates_the_user_and_returns_it(client, db, google_accounts):
    response = sign_in(client, google_accounts)

    assert response.status_code == 200
    user = db.query(User).one()
    assert user.google_sub == "123"
    body = response.json()
    assert body["uid"] == str(user.uid)
    assert body["name"] == "Tom Leon"
    assert body["email"] == "tom@example.com"
    assert "google_sub" not in body


def test_google_sign_in_rejects_a_body_without_a_credential(client):
    assert client.post("/auth/google", json={}).status_code == 422


def test_google_sign_in_rejects_a_token_google_does_not_accept(
    client, db, google_accounts
):
    response = client.post("/auth/google", json={"credential": "garbage"})

    assert response.status_code == 401
    assert db.query(User).count() == 0
    assert "set-cookie" not in response.headers


def test_google_sign_in_answers_503_when_no_client_id_is_configured(client):
    # The real verifier runs here; with no client ID it must stop before asking Google.
    main.app.dependency_overrides[auth.get_google_client_id] = lambda: None

    response = client.post("/auth/google", json={"credential": "anything"})

    assert response.status_code == 503
    assert response.json() == {"detail": "Google sign-in is not configured"}


def test_signing_in_again_with_the_same_google_account_reuses_the_user(
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


def test_google_sign_in_uses_the_email_as_the_name_when_google_sends_none(
    client, google_accounts
):
    response = sign_in(
        client, google_accounts, {"sub": "123", "email": "tom@example.com"}
    )

    assert response.status_code == 200
    assert response.json()["name"] == "tom@example.com"


def test_google_sign_in_answers_503_when_the_database_cannot_be_used(
    client, db, google_accounts, caplog
):
    # No user table any more, so the query fails for real.
    User.__table__.drop(db.get_bind())

    response = sign_in(client, google_accounts)

    assert response.status_code == 503
    assert "no such table" in caplog.text


def test_google_sign_in_sets_a_session_cookie_only_the_browser_can_read(
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


def test_me_returns_the_signed_in_user(client, google_accounts):
    signed_in = sign_in(client, google_accounts)

    response = client.get("/auth/me")

    assert response.status_code == 200
    assert response.json() == signed_in.json()


def test_me_answers_401_when_nobody_is_signed_in(client):
    assert client.get("/auth/me").status_code == 401


def test_me_answers_401_for_a_forged_session_cookie(client):
    # Not signed by the server, so Starlette treats it as no session at all.
    client.cookies.set("session", "garbage")

    assert client.get("/auth/me").status_code == 401


def test_me_answers_401_when_the_user_was_deleted_after_signing_in(
    client, db, google_accounts
):
    sign_in(client, google_accounts)
    db.delete(db.query(User).one())
    db.commit()

    assert client.get("/auth/me").status_code == 401


def test_logout_ends_the_session(client, google_accounts):
    sign_in(client, google_accounts)

    response = client.post("/auth/logout")

    assert response.status_code == 204
    assert client.get("/auth/me").status_code == 401
