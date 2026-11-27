import importlib

import pytest


@pytest.mark.parametrize(
    "env_url",
    [
        "postgresql://app:pw@ep-cool-sun-1234.aws.neon.tech/neondb?sslmode=require",
        "postgres://app:pw@ep-cool-sun-1234.aws.neon.tech/neondb?sslmode=require",
    ],
)
def test_database_url_uses_the_psycopg_driver_for_both_postgres_schemes(
    monkeypatch, env_url
):
    # Neon's Pulumi provider hands out "postgres://..."; SQLAlchemy 2 only accepts
    # "postgresql+psycopg://...", so both spellings must be rewritten.
    monkeypatch.setenv("DATABASE_URL", env_url)
    import config

    importlib.reload(config)
    assert config.database_url.startswith("postgresql+psycopg://app:pw@")
    importlib.reload(config)  # back to the test environment's own URL


@pytest.mark.parametrize(
    "value, expected", [("", False), ("false", False), ("true", True), ("True", True)]
)
def test_session_https_only_is_true_only_when_the_environment_says_true(
    monkeypatch, value, expected
):
    monkeypatch.setenv("SESSION_HTTPS_ONLY", value)
    import config

    importlib.reload(config)
    assert config.session_https_only is expected
    importlib.reload(config)


def test_session_secret_is_a_fresh_random_secret_each_start_when_unset(monkeypatch):
    # A forgotten secret must never make session cookies forgeable; the cost of
    # leaving it unset is only that logins stop surviving a restart.
    monkeypatch.delenv("SESSION_SECRET", raising=False)
    import config

    importlib.reload(config)
    first = config.session_secret
    importlib.reload(config)
    assert len(first) == 64
    assert first != config.session_secret


def test_session_secret_comes_from_the_environment_when_set(monkeypatch):
    monkeypatch.setenv("SESSION_SECRET", "one-long-random-string")
    import config

    importlib.reload(config)
    assert config.session_secret == "one-long-random-string"
    importlib.reload(config)


@pytest.mark.parametrize(
    "value, expected",
    [("", None), ("123.apps.googleusercontent.com", "123.apps.googleusercontent.com")],
)
def test_google_client_id_is_none_when_blank(monkeypatch, value, expected):
    monkeypatch.setenv("GOOGLE_CLIENT_ID", value)
    import config

    importlib.reload(config)
    assert config.google_client_id == expected
    importlib.reload(config)
