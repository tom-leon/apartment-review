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
