import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel

from controllers import auth
import main
from schemas import GoogleCredential


@pytest.fixture
def testing_session():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    return sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db(testing_session):
    db = testing_session()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client(testing_session):
    def override_get_db():
        db = testing_session()
        try:
            yield db
        finally:
            db.close()

    main.app.dependency_overrides[main.get_db] = override_get_db
    yield TestClient(main.app)
    main.app.dependency_overrides.clear()


@pytest.fixture
def google_accounts(client):
    """A stand-in for Google: POST /auth/google accepts each credential added here as
    the claims it maps to, and answers 401 to any other credential."""
    accounts = {}

    def verify_fake_token(body: GoogleCredential) -> dict:
        if body.credential not in accounts:
            raise HTTPException(
                status_code=401, detail="Could not verify the Google sign-in"
            )
        return accounts[body.credential]

    main.app.dependency_overrides[auth.verify_google_token] = verify_fake_token
    return accounts
