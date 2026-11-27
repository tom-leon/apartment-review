import os
import secrets

_DEFAULT_DATABASE_URL = "postgresql+psycopg://tom:123@localhost:5432/apartment_review"

database_url = os.getenv("DATABASE_URL", _DEFAULT_DATABASE_URL)
# Hosted databases hand out "postgres://" (Neon) or "postgresql://"; SQLAlchemy only
# accepts the driver-qualified form.
for _scheme in ("postgresql://", "postgres://"):
    if database_url.startswith(_scheme):
        database_url = database_url.replace(_scheme, "postgresql+psycopg://", 1)
        break

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

# Client ID of the Google OAuth web client the frontend's "Sign in with Google"
# button uses; the API only accepts ID tokens issued for it. Unset = sign-in is off.
google_client_id = os.getenv("GOOGLE_CLIENT_ID") or None

# Signs the session cookie. Unset = a new random secret each start, so a forgotten
# secret can never make cookies forgeable; logins just stop surviving a restart.
session_secret = os.getenv("SESSION_SECRET") or secrets.token_hex(32)

# Secure flag on the session cookie, so browsers only send it over HTTPS. Production
# sets it to "true"; leave it unset for http://localhost.
session_https_only = os.getenv("SESSION_HTTPS_ONLY", "false").lower() == "true"
