from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text

ALEMBIC_INI = Path(__file__).parent.parent / "alembic.ini"
FIRST_MIGRATION = "a52abc977036"


@pytest.fixture
def alembic_config(tmp_path):
    """Alembic, pointed at an empty database of its own."""
    config = Config(ALEMBIC_INI)
    config.set_main_option("sqlalchemy.url", f"sqlite:///{tmp_path}/migrated.db")
    return config


def test_the_migrations_build_the_tables_the_models_describe(alembic_config):
    command.upgrade(alembic_config, "head")

    # Raises when a model was changed without writing a migration for it.
    command.check(alembic_config)


def test_a_database_from_before_alembic_is_taken_over_and_brought_up_to_date(
    alembic_config,
):
    # Before Alembic the app made the first migration's tables itself, so such a
    # database has those tables and no record of any migration.
    command.upgrade(alembic_config, FIRST_MIGRATION)
    engine = create_engine(alembic_config.get_main_option("sqlalchemy.url"))
    with engine.begin() as connection:
        connection.execute(text("DROP TABLE alembic_version"))

    command.upgrade(alembic_config, "head")

    command.check(alembic_config)
