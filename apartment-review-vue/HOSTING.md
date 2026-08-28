# Hosting & Production Cost Notes

Research date: **2026-08-04**. Prices are list prices at that date and drift — re-check before committing.

This covers both halves of the app: this repo (`apartment-review-vue`) and the API in
`apartment-review-fastapi`.

## What we're actually deploying

Knowing the shape of the app narrows the hosting options a lot:

**Frontend (this repo)** — Vue 3 + Vite + TypeScript SPA. PrimeVue, Pinia, `vue-router` in
`createWebHistory` mode. There is no SSR and no server-side runtime: `npm run build` emits a
folder of static files. That means it can go on a pure static/CDN host, which is the cheapest
category of hosting there is, and in practice free.

Two things about the current code affect deployment:

- `vue-router` uses HTML5 history mode, so the host **must** rewrite unknown paths to
  `/index.html` or every URL except `/` will 404 on refresh.
- `src/stores/apartment.ts` calls a **relative** path (`fetch("/api/apartments")`), so in
  production the API has to be reachable on the same origin as the frontend, or those calls
  need to change to an absolute URL (and then the API needs CORS headers, which it currently
  does not send — there is no `CORSMiddleware` in `main.py`).

**Backend (`apartment-review-fastapi`)** — FastAPI + SQLModel + Uvicorn, talking to PostgreSQL
via `psycopg2-binary`. This is a long-running process, so it cannot live on a static host and
cannot go on a free tier that sleeps on idle. It already has a working `Dockerfile`, which means
every container-based platform below is a candidate with no extra work.

**Database** — PostgreSQL. The schema is small (three tables: `user`, `apartment`, `review`) and
uses `DECIMAL` lat/long plus a location index, so any standard managed Postgres works. No
PostGIS is required today, but note that if apartment search by radius ever gets added, PostGIS
availability becomes a selection criterion — Neon and Supabase both support it, some smaller
hosts don't.

## Frontend hosting

| Host | Free tier | Cheapest paid | SPA rewrite support | Notes |
|---|---|---|---|---|
| **Cloudflare Pages** | Unlimited bandwidth + unlimited static requests, 500 builds/mo | $20/mo (Pro — only buys more concurrent builds) | Yes, via `_redirects` or `_routes.json` | No commercial-use restriction. Can also reverse-proxy `/api/*` to the backend, which solves the relative-URL problem for free. |
| **Vercel** | 100 GB transfer, 1M edge requests/mo | $20/user/mo (Pro) | Yes, automatic for SPAs | Hobby tier's terms of service **exclude commercial use**. Fine while this is a side project, a problem the day it earns money. |
| **Netlify** | 300 credits/mo (~15 GB, at 20 credits/GB) | $9/mo (Personal), $20/mo (Pro) | Yes, via `_redirects` | Same commercial-use restriction on the free tier. Credit model makes cost harder to predict than Cloudflare's flat "unlimited". |
| **GitHub Pages** | Free, unlimited for public repos | n/a | Awkward — needs a 404.html hack | Both repos are private, and it can't proxy the API. Not a fit. |
| **S3 + CloudFront** | 12-month trial only | ~$1–3/mo at low traffic + $0.085/GB | Yes, via CloudFront error-page rules | Cheap but not free, and by far the most setup. Only worth it if you're already committed to AWS. |

**Recommendation: Cloudflare Pages.** It's free with genuinely unlimited bandwidth, has no
commercial-use catch in its terms, handles the SPA rewrite with a two-line `_redirects` file, and
its ability to proxy `/api/*` to the backend means the frontend and API share one origin. That
last point is worth more than it sounds: it removes the need to touch `stores/apartment.ts`, and
it removes the need for CORS on the API entirely.

## Backend hosting

The FastAPI service needs a process that stays awake. Free tiers that spin down on idle (Render's
free web service, in particular) make the first request after a quiet period take 30+ seconds,
which is unacceptable for a user-facing API.

| Host | Cheapest usable tier | Specs | Notes |
|---|---|---|---|
| **Railway** | $5/mo Hobby (includes $5 usage credit) | Usage-metered: ~$0.0000039/GB-sec RAM, ~$0.0000077/vCPU-sec | Deploys the existing Dockerfile as-is. A low-traffic FastAPI app fits inside the $5 credit. Egress $0.05/GB. Postgres can be added as a service in the same project. |
| **Render** | $7/mo Starter | 512 MB RAM, 0.5 CPU | Never sleeps on paid tier. Free tier sleeps — don't use it for this. Managed Postgres from $6/mo (Basic, 256 MB). Simplest dashboard of the three. |
| **Fly.io** | ~$2–5/mo per Micro VM, pay-as-you-go | shared-cpu-1x, 256 MB–1 GB | No meaningful free tier any more. Best option if you want the API running in a region close to users (e.g. Sydney for an Australian audience) — latency matters for a search-driven site. |
| **DigitalOcean App Platform** | $5/mo | 512 MB RAM, 1 shared vCPU, 50 GiB transfer | Predictable flat pricing, no usage metering surprises. Their dev Postgres is +$7/mo, which is worse value than Neon's free tier. |
| **Self-managed VPS** (Hetzner CX22 / DO Droplet) | ~$4–6/mo flat | Hetzner: 2 vCPU / 4 GB RAM. DO basic: 1 vCPU / 512 MB–1 GB | Cheapest per unit of compute by a wide margin, and one box can run the API, Postgres, and Nginx serving the built frontend — which also makes the same-origin problem disappear. Cost is your time: OS patching, SSL renewal via Certbot, backups, and monitoring are all yours. |

**Recommendation: Railway Hobby ($5/mo) to start**, moving to a VPS only if the bill grows or you
want the ops control. Railway takes the existing Dockerfile without modification and its $5 credit
covers a low-traffic app, so the effective cost is $5/mo flat until there's real usage. If most
users will be in Australia, Fly.io in `syd` is worth the slightly fiddlier setup for the latency.

## Database hosting

| Host | Free tier | Cheapest paid | Notes |
|---|---|---|---|
| **Neon** | 0.5 GB storage, 100 CU-hours/mo, 5 GB egress — permanent | Pay-as-you-go: $0.106/CU-hr + $0.35/GB-mo | Does not force-pause an idle project the way Supabase does. Scales to zero, so a quiet app costs near nothing. Branching is handy for staging. |
| **Supabase** | 500 MB storage, 5 GB egress | $25/mo (Pro) | **Pauses the project after one week of inactivity** — bad for a low-traffic production site. You'd be paying $25/mo to avoid that, and we don't need its auth/storage extras. |
| **Render Postgres** | 30 days only, then paid | $6/mo (Basic, 256 MB RAM) | Reasonable if the backend is already on Render — one vendor, one bill. |
| **Railway Postgres** | Inside the plan's usage credit | Usage-metered | Same-project networking with the API, so no egress cost between them. Backups need configuring. |
| **On your own VPS** | Free (included in the VPS) | — | Zero marginal cost, but backups and point-in-time recovery are entirely your responsibility. For a site holding user reviews, that's a real risk to accept knowingly. |

**Recommendation: Neon free tier.** 0.5 GB holds a very large number of text reviews, it never
force-pauses, and moving to pay-as-you-go later is a pricing change rather than a migration.

## Recommended combinations

**Option 1 — cheapest managed setup (~$5/mo, recommended to launch):** Cloudflare Pages (free) for
this repo, Railway Hobby ($5/mo) for the API, Neon free tier for Postgres. Configure Cloudflare to
proxy `/api/*` to the Railway URL so both live on one origin. Total roughly $5/mo plus ~$10/yr for
a domain, and almost nothing to operate.

**Option 2 — cheapest at real traffic (~$5/mo flat, more work):** Cloudflare Pages (free) plus a
single Hetzner CX22 (~$5/mo, 2 vCPU / 4 GB) running the API, Postgres, and Nginx via Docker
Compose. Far more compute for the same money and no usage metering, but you own patching, SSL,
and backups. Worth switching to if Railway's metered bill starts climbing.

**Option 3 — fewest moving parts (~$13/mo):** Render for everything — static site for the
frontend (free), Starter web service for the API ($7/mo), Render Postgres ($6/mo). One vendor, one
dashboard, one bill. Costs more than option 1 but is the least to think about.

Domain registration is ~$10–15/yr on any of these. Cloudflare Registrar sells at wholesale cost
with no markup and no first-year-discount trick, so it's usually the cheapest — and convenient if
Pages is already in use.

## Things to fix before this goes to production

These are not hosting decisions, but they will bite on launch day and some of them influence the
setup above.

**Passwords are stored in plaintext.** `models.py` declares `password: str` on `User` and
`main.py`'s `create_user` writes it straight to the database and then returns the whole `User`
object — password included — in the response. This needs a hashing library (`passlib[bcrypt]` or
`argon2-cffi`) and a response schema that omits the field. `schemas.py` already defines a correct
`UserResponse` without the password; it just isn't wired up. Do this before any real user data
exists, because it can't be retrofitted afterwards.

**No migrations.** `main.py` calls `SQLModel.metadata.create_all(engine)` at import time. That
creates missing tables but never alters existing ones, so the first schema change against a
production database will silently do nothing and the app will fail on a missing column. Add
Alembic before the first deploy. This is much cheaper to do now than after there's data to
preserve.

**No CORS middleware,** which is fine only if the same-origin proxy in option 1 is used. If the
frontend ever calls the API on a different hostname, add `CORSMiddleware` with an explicit
allow-list — not `["*"]`, since these endpoints will eventually carry credentials.

**No authentication on any endpoint.** `POST /apartment` and `POST /user` are open to the
internet. A public review site with unauthenticated writes will be filled with spam within days
of being indexed. Rate limiting at the Cloudflare layer helps but is not a substitute for auth.

**The frontend Dockerfile is development-only** — it runs `npm run dev` on port 5173. It is not
usable for production. This doesn't matter if the frontend goes on Cloudflare Pages (which runs
`npm run build` itself and serves `dist/`), but if the VPS route in option 2 is chosen, it needs a
multi-stage build that runs `npm run build` and serves `dist/` from Nginx.

**Environment variable naming is inconsistent.** `.env.development` sets `API_URL`, but Vite only
exposes variables prefixed with `VITE_` to client code, and `docker-compose.yml` sets
`VITE_API_URL`. Neither is actually read anywhere — the store hardcodes `/api/apartments`. Pick
one approach: either commit to the same-origin proxy and delete the unused vars, or introduce a
`VITE_API_BASE_URL` and use it in the store.

**Hardcoded database credentials.** `database.py` falls back to
`postgresql://tom:123@localhost:5432/apartment_review` and `docker-compose.yml` hardcodes the same
`tom`/`123` pair. Fine locally. In production, `DATABASE_URL` must come from the platform's secret
store, and the fallback should arguably raise instead of defaulting, so a misconfigured deploy
fails loudly rather than quietly trying to reach a database that isn't there.

**Minor:** `datetime.utcnow` is deprecated in Python 3.12+ (use
`datetime.now(timezone.utc)`); the `version: "3.8"` key in `docker-compose.yml` is obsolete and
ignored by modern Compose; and `utils.py` and `example_endpoints.py` contain working logic
(including `get_or_create_apartment`) that `main.py` never imports, so the live API is only three
endpoints.

## Sources

- [Cloudflare Pages pricing](https://pages.cloudflare.com/)
- [Vercel pricing](https://vercel.com/pricing)
- [Netlify pricing](https://www.netlify.com/pricing/)
- [Render pricing](https://render.com/pricing)
- [Railway pricing](https://railway.com/pricing)
- [Fly.io pricing](https://fly.io/pricing)
- [DigitalOcean App Platform pricing](https://www.digitalocean.com/pricing/app-platform)
- [DigitalOcean Droplet pricing](https://www.digitalocean.com/pricing/droplets)
- [Neon pricing](https://neon.com/pricing)
- [Supabase pricing](https://supabase.com/pricing)
