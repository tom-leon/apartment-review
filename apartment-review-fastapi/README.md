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
`postgresql://tom:123@localhost:5432/apartment_review` (`database.py`) if it isn't set.

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

- **No CORS middleware.** The production frontend and backend are on different origins
  (`*.pages.dev` vs `*.ondigitalocean.app`), and `main.py` doesn't set up `CORSMiddleware` yet —
  cross-origin requests from the deployed frontend will fail until it's added.
- **No auth on any endpoint.** `POST /apartment` and `POST /user` are open to the internet.
- **Passwords are stored in plaintext.** `models.py`'s `User.password` is written and returned
  as-is; needs hashing (e.g. `passlib[bcrypt]`) before real accounts exist.
- **No migrations.** `main.py` calls `SQLModel.metadata.create_all(engine)` on startup, which
  creates missing tables but never alters existing ones. Add Alembic before the first schema
  change against production data.

## Dependencies

Managed with [uv](https://docs.astral.sh/uv/) (`pyproject.toml` + `uv.lock`). Python 3.10+.

```bash
uv sync
uv run uvicorn main:app --reload
```
