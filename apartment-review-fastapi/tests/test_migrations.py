from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config

ALEMBIC_INI = Path(__file__).parent.parent / "alembic.ini"


@pytest.fixture
def alembic_config(tmp_path):
    """Alembic, pointed at an empty database of its own."""
    config = Config(ALEMBIC_INI)
    config.set_main_option("sqlalchemy.url", f"sqlite:///{tmp_path}/migrated.db")
    return config


def test_a_new_database_gets_exactly_the_tables_the_app_expects(alembic_config):
    command.upgrade(alembic_config, "head")

    # Raises when a model was changed without writing a migration for it.
    command.check(alembic_config)
