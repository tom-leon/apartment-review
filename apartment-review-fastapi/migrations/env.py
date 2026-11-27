"""What Alembic runs: which database to change, and what its tables should look like."""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine
from sqlmodel import SQLModel

import models  # noqa: F401 (puts the tables on SQLModel.metadata)
from config import database_url

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name, disable_existing_loggers=False)

# The app's database, unless the caller (the tests) points Alembic at another one.
url = config.get_main_option("sqlalchemy.url") or database_url

with create_engine(url).connect() as connection:
    context.configure(
        connection=connection,
        target_metadata=SQLModel.metadata,
        # Batch mode lets the same migrations run on SQLite, which the tests use.
        render_as_batch=True,
    )
    with context.begin_transaction():
        context.run_migrations()
