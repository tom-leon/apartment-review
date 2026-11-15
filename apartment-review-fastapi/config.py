import os

_DEFAULT_DATABASE_URL = "postgresql+psycopg://tom:123@localhost:5432/apartment_review"

database_url = os.getenv("DATABASE_URL", _DEFAULT_DATABASE_URL)
if database_url.startswith("postgresql://"):
    database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)

_DEFAULT_CORS_ORIGINS = "http://localhost:5173,http://localhost:5273"

# Browser origins allowed to call this API, comma-separated. Defaults cover the Vite
# dev server and the port Docker Compose maps the frontend to.
cors_origins = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", _DEFAULT_CORS_ORIGINS).split(",")
    if origin.strip()
]

# Google Maps Platform key for Street View photos of the buildings. It ends up in
# <img> addresses that every visitor can read, so in the Google Cloud console limit
# it to this site's address and to the Street View Static API. Unset = no photos.
google_maps_api_key = os.getenv("GOOGLE_MAPS_API_KEY") or None
