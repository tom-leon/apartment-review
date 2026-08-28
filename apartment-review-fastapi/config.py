import os

_DEFAULT_DATABASE_URL = "postgresql+psycopg://tom:123@localhost:5432/apartment_review"

database_url = os.getenv("DATABASE_URL", _DEFAULT_DATABASE_URL)
if database_url.startswith("postgresql://"):
    database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)
