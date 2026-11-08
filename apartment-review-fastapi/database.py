from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config import database_url


engine = create_engine(database_url)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# SQLModel uses SQLModel as the base instead of declarative_base()
# We'll create tables using SQLModel.metadata.create_all()
