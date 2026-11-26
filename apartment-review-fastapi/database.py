from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config import database_url


# pool_pre_ping: Neon suspends an idle database, which silently kills pooled
# connections; check each one before use so the next request reconnects
# instead of hanging.
engine = create_engine(database_url, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# SQLModel uses SQLModel as the base instead of declarative_base()
# We'll create tables using SQLModel.metadata.create_all()
