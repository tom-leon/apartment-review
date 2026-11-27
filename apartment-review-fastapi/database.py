from typing import Annotated

from fastapi import Depends
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from config import database_url


# pool_pre_ping: Neon suspends an idle database, which silently kills pooled
# connections; check each one before use so the next request reconnects
# instead of hanging.
engine = create_engine(database_url, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# The tables themselves are made and changed by the Alembic migrations in migrations/.


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]
