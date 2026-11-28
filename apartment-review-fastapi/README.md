# apartment-review-fastapi

Backend API for the apartment review app: FastAPI + SQLModel over PostgreSQL.

## Local stack (Docker Compose)

This folder has no `docker-compose.yml` of its own — it's run as one of three services defined in
`apartment-review-vue/docker-compose.yml` (the frontend folder). From there:

```bash
cd ../apartment-review-vue
docker-compose up
```

That builds this folder's `Dockerfile` and starts it alongside Postgres and the frontend. See that
folder's `DOCKER_GUIDE.md` for the local port mapping (the backend lands on **localhost:8100**, not
8000 — the guide documents why).

Locally the app reads `DATABASE_URL` from the environment, falling back to
`postgresql+psycopg://tom:123@localhost:5432/apartment_review` (`config.py`) if it isn't set.

`CORS_ORIGINS` (comma-separated browser origins allowed to call the API) works the same way,
defaulting to the Vite dev server `http://localhost:5173` and the Docker-mapped
`http://localhost:5273` (`config.py`). In production Pulumi sets it to the Cloudflare Pages domain.

`GOOGLE_MAPS_API_KEY` (optional) turns on street photos of the buildings: `GET /apartments/recent`
then returns a Google Street View address in `photo_url` for each apartment. Without it
`photo_url` is `null` and the home page shows a placeholder. The key is readable in those
addresses, so limit it in the Google Cloud console to this site and to the Street View Static API.

`GOOGLE_CLIENT_ID` turns on Google sign-in: the client ID of the Google OAuth web client that the
frontend's "Sign in with Google" button uses. `POST /auth/google` takes the button's ID token as
`{"credential": ...}`, creates the user on their first sign-in and starts a session (an HttpOnly
cookie); `GET /auth/me` returns the signed-in user; `POST /auth/logout` ends the session. Unset =
`POST /auth/google` answers 503.

`SESSION_SECRET` signs the session cookie. In production set it to one long random string; unset,
the API makes a new one each start, so logins stop surviving a restart but cookies can never be
forged.

`SESSION_HTTPS_ONLY=true` marks the session cookie `Secure` (sent over HTTPS only). Set it in
production; leave it unset for `http://localhost`.

## Production stack

| Layer | Service | Plan |
|---|---|---|
| API (this folder) | DigitalOcean App Platform | `apps-s-1vcpu-0.5gb` — $5/mo |
| Database | Neon (managed Postgres) | Free tier — `aws-ap-southeast-1` |
| Frontend | Cloudflare Pages | Free tier |

The backend deploys straight from this folder's `Dockerfile` — DigitalOcean's App Platform builds
and runs it as-is, no changes needed for that part. It's a plain `uvicorn main:app --host 0.0.0.0
--port 8000`, and `DATABASE_URL` is injected at deploy time as a secret env var pointing at the
Neon connection string.

### Infrastructure as code

All three production services (DigitalOcean app, Neon project, Cloudflare Pages project) are
defined in one Pulumi (TypeScript) program, at the repo root:

```
../infra/
```

See that folder's `README.md` for the one-time GitHub authorizations, the API tokens/secrets to
configure, and the `pulumi up` / `pulumi destroy` commands. Nothing needs to run from this folder to
deploy it — the Pulumi stack points DigitalOcean at this folder of `tom-leon/apartment-review`
(`main` branch), and GitHub Actions asks DigitalOcean to redeploy after the backend tests pass
(`.github/workflows/backend.yml`).

### Known gaps before this is safe to point real users at

- **Creating an apartment needs no sign-in.** `POST /apartment` and `POST /apartments/from-osm`
  are open to the internet. Posting, editing and deleting a review do need a signed-in user.
- **Reviews are not checked before they show.** A posted review is public at once.

## Database migrations

Table changes are [Alembic](https://alembic.sqlalchemy.org) migrations in `migrations/versions/`.

- After changing a file in `models/`: `uv run alembic revision --autogenerate -m "what changed"`,
  then commit the new file with the model change. `tests/test_migrations.py` fails (locally and
  in CI) when the models and the migrations disagree.
- Applying them is automatic: the container's start command is `alembic upgrade head`, then the
  API ([Dockerfile](Dockerfile), and the same in Docker Compose). Every deploy therefore brings
  the database up to date first, and a migration that fails stops the new version from starting.

## Dependencies

Managed with [uv](https://docs.astral.sh/uv/) (`pyproject.toml` + `uv.lock`). Python 3.10+.

```bash
uv sync
uv run uvicorn main:app --reload
```
