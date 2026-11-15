# CI/CD plan — apartment-review (Vue + FastAPI)

## Goal

- Every push to `main` runs the backend tests and the frontend tests + build, automatically.
- The backend goes live only after its tests pass.
- Cloudflare builds and publishes the frontend from `main` by itself.
- Single contributor, no pull requests: `main` is the only branch.

## Progress

![](https://img.shields.io/badge/PROGRESS-4%2F7_TASKS_DONE-f0ad4e?style=for-the-badge) ![](https://img.shields.io/badge/STEPS-24%2F40-f0ad4e?style=for-the-badge) ![](https://img.shields.io/badge/CI_ON_MAIN-GREEN-2ea44f?style=for-the-badge) ![](https://img.shields.io/badge/PRODUCTION-NOT_YET-d73a49?style=for-the-badge)

```
TASKS   🟩🟩🟩🟩⬜⬜⬜   4 / 7
STEPS   🟩🟩🟩🟩🟩🟩🟩🟩🟩🟩🟩🟩⬜⬜⬜⬜⬜⬜⬜⬜   24 / 40
```

| # | Task | Status | Steps |
|---|---|---|---|
| 1 | Make black and flake8 pass | ![](https://img.shields.io/badge/DONE-2ea44f?style=flat-square) | 🟩🟩🟩🟩🟩🟩🟩 7/7 |
| 2 | Backend CI workflow | ![](https://img.shields.io/badge/DONE-2ea44f?style=flat-square) | 🟩🟩🟩🟩 4/4 |
| 3 | Frontend CI workflow | ![](https://img.shields.io/badge/DONE-2ea44f?style=flat-square) | 🟩🟩🟩🟩 4/4 |
| 4 | Pulumi points at the monorepo | ![](https://img.shields.io/badge/DONE-2ea44f?style=flat-square) | 🟩🟩🟩🟩🟩🟩🟩🟩🟩 9/9 |
| 5 | **First production deploy (manual)** | ![](https://img.shields.io/badge/NOT_STARTED-d73a49?style=flat-square) | ⬜⬜⬜⬜⬜⬜ 0/6 |
| 6 | Backend deploy job | ![](https://img.shields.io/badge/BLOCKED-8b949e?style=flat-square) 🔒 needs Task 5 step 5 | ⬜⬜⬜⬜ 0/4 |
| 7 | Dependabot | ![](https://img.shields.io/badge/READY-0969da?style=flat-square) | ⬜⬜⬜⬜⬜⬜ 0/6 |

**Milestones**

- ✅ First green run — `frontend` run 42473923612, 22 s (2026-11-08)
- ✅ First failure, fixed — `backend` run 42473923633 failed in 6 s: `setup-uv@v10` does not exist
- ✅ Pinned to `@v10.3.3`; next run green in 50 s
- ✅ Tests: backend 4 → 6, frontend 0 → 4
- ✅ CORS middleware done ahead of the plan (`ce61742`)
- ✅ `VITE_API_URL` wiring done ahead of the plan (`d424bee`)
- ✅ `infra/` moved to the repo root, beside the two apps
- ✅ Repo public since 2026-11-08

**🔴 Next: Task 5, the first production deploy.**

- The one manual task: dashboard clicks and real API tokens.
- Run from `infra/`.

---

## Architecture

- Two small GitHub Actions workflows, one per app. Each runs only when its folder changes.
- Backend workflow: lint + tests + Docker build, then asks DigitalOcean to redeploy.
- Frontend workflow: Vitest tests + build. Reports only.
- Cloudflare Pages builds and deploys `main` on its own, with the same build command.
- The Pulumi program: fixed so it runs, pointed at the monorepo, told to let CI trigger backend deploys.

**Tech stack:** GitHub Actions · uv + pytest + black + flake8 · npm + vue-tsc + Vite · Docker · Pulumi (TypeScript) · DigitalOcean App Platform · Cloudflare Pages · Neon Postgres.

**Spec:** the *Why*, *What's true today* and *Design* sections of this file.

---

## Why

Before this plan:

- Nothing checked a change after it landed on `main`.
- Nothing was deployed anywhere, so the app could not be put in front of a person.
- A broken commit was found by hand, days later.
- "Deploy" was a manual afternoon that had never actually been done.

After this plan:

- A red check on `main` says within ~3 minutes that tests, formatting or the Docker image broke.
- A push to `main` ships the backend by itself, and only if green.
- The frontend ships itself on every `main` build.
- Production exists.

## What's true today (checked 2026-10-13, before Task 1)

| Area | Fact at the start | Evidence |
|---|---|---|
| CI | No workflows anywhere. GitHub Actions is enabled on the repo | no `.github/` folder; `gh api repos/.../actions/permissions` → `enabled: true` |
| Repo | Private, on GitHub Free. **No branch protection or rulesets** (403 "Upgrade to GitHub Pro or make this repository public") | `gh api .../branches/main/protection` |
| Backend tests | 4 pass, on an in-memory SQLite database, so **CI needs no Postgres** | `uv run pytest` ([conftest.py](apartment-review-fastapi/tests/conftest.py)) |
| Backend format | `black --check` fails: 6 files, formatting only, ~330 diff lines | `uv run black --check .` |
| Backend lint | `flake8` with a black-compatible config leaves 10 real issues after black: 8 unused imports, 2 long lines | `uv run flake8 .` |
| Backend lint config | None. So flake8 also scans `.venv` and reports 28,000 "errors" | `uv run flake8 .` |
| Backend lockfile | `uv.lock` is in sync with `pyproject.toml` | `uv lock --check` → ok |
| Backend Docker | [Dockerfile](apartment-review-fastapi/Dockerfile) builds | `docker build .` → exit 0 |
| Frontend | `npm ci`, `npm test` (Vitest, 2 tests) and `npm run build` (type-check + Vite build) pass on Node 22 | [package.json](apartment-review-vue/package.json) |
| Frontend lint | **None exists** | [package.json](apartment-review-vue/package.json) |
| Infra | The Pulumi project file is malformed, so Pulumi can't load it | `pulumi stack ls` → "Configuration key 'cloudflare:apiToken' is namespaced and must provide an attribute 'value'" ([Pulumi.yaml:4-8](infra/Pulumi.yaml#L4-L8)) |
| Infra | With the bad block removed it loads and shows **no stacks: nothing has ever been deployed** | `pulumi stack ls` |
| Infra | The program still names the two pre-monorepo repos (`apartment-review-fastapi`, `apartment-review-vue`). Both still exist on GitHub, unarchived, last pushed 2026-02-06 | [index.ts:14-17](infra/index.ts#L14-L17) |
| GitHub account | Renamed from `yilin-chao` to `tom-leon` (checked 2026-11-08). Old URLs redirect, so `git push` still works. DigitalOcean, Cloudflare and Pulumi must use `tom-leon` | `gh api user` → `tom-leon`; `gh repo view yilin-chao/apartment-review` → url `tom-leon/apartment-review` |

**Changed since:**

- Repo is **public** (so branch protection is now available, if ever wanted).
- Backend format and lint green.
- 6 backend tests, 4 frontend tests.
- Pulumi loads.
- Program points at `tom-leon/apartment-review`.

## Design

### How a change flows

```
you push to main
  ├─ backend.yml   (runs only if apartment-review-fastapi/** changed)
  │     test:   checkout → uv sync --locked → black --check → flake8 → pytest → docker build
  │     deploy: (only if test passed)  doctl apps create-deployment <app id> --wait
  │               → DigitalOcean rebuilds the Dockerfile from main and swaps it in.
  │                 If the build fails, the old version stays up.
  ├─ frontend.yml  (runs only if apartment-review-vue/** changed)
  │     checkout → npm ci → npm test → npm run build   (vitest, then vue-tsc type-check + vite build)
  │     red here does NOT stop Cloudflare (see decision 4)
  └─ Cloudflare Pages builds main by itself (npm run build inside apartment-review-vue/)
        and publishes dist/. If the build fails, the previous deployment stays live.
```

Terms, once:

- **CI** = the checks that run on every change.
- **CD** = the step that puts a change live.
- **Workflow** = one YAML file that GitHub Actions runs.
- **`doctl`** = DigitalOcean's command-line tool.
- **App Platform** = DigitalOcean's "give it a Dockerfile and it runs it" service.
- **Cloudflare Pages** = a static-site host that builds straight from a Git repo.

### Options considered

| | A. Platforms auto-deploy, Actions only reports | **B. Actions gates the backend deploy (this plan)** | C. Build once, deploy the exact artifact |
|---|---|---|---|
| Backend goes live by | DigitalOcean watches `main` | Actions, after tests pass, runs `doctl apps create-deployment` | Actions builds the image → DigitalOcean Container Registry → app runs that image |
| Frontend goes live by | Cloudflare watches `main` | Cloudflare watches `main` (its build *is* our only frontend check) | Actions runs `wrangler pages deploy dist` |
| Secrets to put in GitHub | 0 | 1 token + 1 app id | DigitalOcean token, Cloudflare token, registry login |
| Bad backend commit pushed | goes live | **blocked** | **blocked** |
| Tested == deployed? | no | same commit, rebuilt by DigitalOcean | exactly the tested image |
| Extra code | none | ~10 lines of YAML | ~60 lines of YAML + Pulumi rewrite (image source, direct-upload Pages) |

**Recommendation: B.**

- Smallest change that makes tests actually gate a deploy.
- A gates nothing.
- C ships the exact image CI tested. That only matters once the Docker build isn't reproducible, and it costs a Pulumi rewrite.
- Move to C later if a DigitalOcean build ever differs from CI (see the Dockerfile note under *Found while planning*).

### Decisions you can still flip

1. **Approach B** over A or C (above).
2. **Lint in CI.**
   - `black` and `flake8` are already dev dependencies.
   - The plan runs them; Task 1 makes them pass (10 one-line fixes + a black reformat).
   - To skip: drop Task 1 and the two lint lines in Task 2.
3. **Frontend checks.**
   - Vitest is installed with store tests, so CI runs `npm test` then `npm run build`.
   - ESLint and Prettier are still not installed. Adding them is its own decision.
4. **Frontend tests don't gate the frontend deploy.**
   - Cloudflare deploys `main` as soon as its own build passes.
   - A failing Vitest test only shows red in Actions.
   - To gate it too: `productionDeploymentEnabled: false` in Pulumi, a Cloudflare deploy hook (a secret URL that starts a build when POSTed), and a `deploy` job in `frontend.yml` that `curl -X POST`s it after tests.
   - About 8 lines plus one more secret. Not in this plan.

## Global constraints

- **Python 3.10** everywhere: [.python-version](apartment-review-fastapi/.python-version), [Dockerfile](apartment-review-fastapi/Dockerfile) `python:3.10-slim`.
- **uv only** for dependencies; never `uv pip` ([CLAUDE.md](apartment-review-fastapi/CLAUDE.md)).
- **Node 22**: [.nvmrc](apartment-review-vue/.nvmrc), `engines >=22.12.0`.
- **`npm ci`** for installs (uses `package-lock.json` exactly).
- **Local `npm test` needs Node 22** (`nvm use 22`); jsdom 30 refuses Node 20.
- **Action versions** as of 2026-11-08: `actions/checkout@v7`, `actions/setup-node@v7`, `astral-sh/setup-uv@v10.3.3`, `digitalocean/action-doctl@v2`.
  - setup-uv publishes **no floating `v10` tag**; the first run failed with "unable to find version `v10`".
  - So it is pinned to the full version. Dependabot (Task 7) will bump it.
  - `action-doctl@v2` is a *branch*, not a tag, and resolves fine.
- **Pulumi providers** stay as pinned in [infra/package.json](infra/package.json).
  - Cloudflare provider v5 has `buildConfig.rootDir` but **no** build-watch-path fields. That stays a dashboard setting.
- **Australian English** in code and docs.
- **Git:** single contributor, no PRs, straight to `main`. One-line commit messages, no `feat:` prefix.
- **Cloud:** every create/change in DigitalOcean, Cloudflare, Neon or Pulumi Cloud is a deliberate manual step, never automated from a plan. Task 5 is run by hand.

## Review focus

Things the design implies but no unit test covers.

| # | If this happens… | …then CI must | Pinned by | Task |
|---|---|---|---|---|
| 1 | `pyproject.toml` edited without re-locking | **fail**, not quietly install something else | `uv sync --locked` | 2 |
| 2 | Two pushes to `main` minutes apart | **queue** the second deploy, not race or cancel the first | `concurrency: backend-production` on the deploy job | 6 |
| 3 | A push changes only a workflow file | still run that workflow | the workflow file listed in its own `paths` | 2, 3 |
| 4 | The deploy job never checks out the repo | not fail with "no such directory" | `defaults.run.working-directory` scoped to the `test` job only | 2, 6 |
| 5 | Backend Dockerfile breaks | fail in Actions before the deploy job, not on DigitalOcean | `docker build .` in the test job | 2 |
| 6 | A `deploy` job exists before its secrets do | not go red on every push | task order: Task 6 only after Task 5 sets the secret and variable | 5, 6 |
| 7 | A Dependabot PR triggers the backend workflow | not run `deploy` (no secrets on PR runs; nothing ships from a PR) | `if: github.event_name == 'push'` | 7 |

## How to run this plan

- ✅ Tasks 1–4: committed and pushed to `main` together.
  - That push touched both app folders, so it proved Tasks 2 and 3 work.
- 🔴 Task 5: run by hand.
- 🔒 Task 6: one more commit to `main`, verified by that push.
- 🔵 Task 7: any time after Task 3.

---

## ✅ Task 1: Make black and flake8 pass (backend)

![](https://img.shields.io/badge/TASK_1-DONE-2ea44f?style=for-the-badge) 🟩🟩🟩🟩🟩🟩🟩 **7/7** · commit `6ae894a` · 2026-11-08

**Files**

- Create: `apartment-review-fastapi/.flake8`
- Edit by hand: [database.py](apartment-review-fastapi/database.py), [example_endpoints.py](apartment-review-fastapi/example_endpoints.py), [schemas.py](apartment-review-fastapi/schemas.py), [utils.py](apartment-review-fastapi/utils.py)
- Reformatted by black: [main.py](apartment-review-fastapi/main.py), [models.py](apartment-review-fastapi/models.py) and the four above

**Interfaces**

- Result: `uv run black --check .`, `uv run flake8 .` and `uv run pytest` all exit 0.
- Task 2 relies on that.

- [x] ✅ **Step 1: Add the flake8 config**
  - Why: black uses 88-column lines; flake8 defaults to 79 and scans `.venv`.
  - Create `apartment-review-fastapi/.flake8`:

```ini
[flake8]
max-line-length = 88
extend-ignore = E203,W503
exclude = .venv
```

- `E203`/`W503`: the two rules black deliberately breaks (whitespace before `:` in slices, line breaks before operators).

- [x] ✅ **Step 2: Let black reformat**
  - Run: `cd apartment-review-fastapi && uv run black .`
  - Expected: `6 files reformatted, 3 files left unchanged.`
  - Formatting only; nothing behavioural.

- [x] ✅ **Step 3: See what flake8 still wants**
  - Run: `uv run flake8 .`
  - Expected: exactly these 10 (line numbers are after black):

```
./database.py:3:1: F401 'sqlmodel.SQLModel' imported but unused
./example_endpoints.py:17:1: F401 'datetime.datetime' imported but unused
./example_endpoints.py:20:1: F401 'models.Apartment' imported but unused
./example_endpoints.py:20:1: F401 'models.User' imported but unused
./example_endpoints.py:21:1: F401 'schemas.ApartmentCreate' imported but unused
./example_endpoints.py:28:1: F401 'utils.calculate_apartment_average_rating' imported but unused
./example_endpoints.py:141:89: E501 line too long (94 > 88 characters)
./schemas.py:1:1: F401 'pydantic.field_validator' imported but unused
./utils.py:4:1: F401 'schemas.ApartmentCreate' imported but unused
./utils.py:20:89: E501 line too long (90 > 88 characters)
```

- `example_endpoints.py` is not imported by anything, so removing its unused imports changes nothing at runtime.

- [x] ✅ **Step 4: Remove the 8 unused imports**
  - `database.py` — delete line 3:

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel          # ← delete this line

from config import database_url
```

- `example_endpoints.py` — the import block becomes:

```python
from typing import List
from uuid import UUID

from database import SessionLocal
from models import Review
from schemas import (
    OSMAddressData,
    ApartmentResponse,
    ReviewCreate,
    ReviewResponse,
)
from utils import (
    get_or_create_apartment,
    get_apartment_by_id,
    get_apartments_by_location,
    get_reviews_for_apartment,
    get_user_review_for_apartment,
)
```

- Removed: `from datetime import datetime`; `Apartment, User` from the models line; `ApartmentCreate,`; `calculate_apartment_average_rating,`.
- `schemas.py` line 1:

```python
from pydantic import BaseModel, Field
```

- `utils.py` line 4:

```python
from schemas import OSMAddressData
```

- [x] ✅ **Step 5: Wrap the 2 long lines**
  - `example_endpoints.py`, inside `create_review` (the only `HTTP_409_CONFLICT` in the file):

```python
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You have already reviewed this apartment. "
            "Use PUT to update your review.",
        )
```

- `utils.py`, the `get_or_create_apartment` docstring:

```python
    Returns:
        Tuple of (Apartment, created) where created is True if a new apartment
        was created
    """
```

- [x] ✅ **Step 6: Verify all three are green**
  - Run: `uv run black --check . && uv run flake8 . && uv run pytest -q`
  - Expected: `All done!`, no flake8 output, `4 passed`.
  - If black wants to re-wrap the two edited lines: `uv run black .` once more, then re-run the check.

- [x] ✅ **Step 7: Commit** — `6ae894a`, pushed 2026-11-08
  - Message: `make black and flake8 pass`

---

## ✅ Task 2: Backend CI workflow

![](https://img.shields.io/badge/TASK_2-DONE-2ea44f?style=for-the-badge) 🟩🟩🟩🟩 **4/4** · commit `2107b48` · 2026-11-08

**Files**

- Create: `.github/workflows/backend.yml`

**Interfaces**

- Produces a job named `test`.
- Task 6's `deploy` job depends on it via `needs: test`. The job name must stay `test`.

- [x] ✅ **Step 1: Write the workflow**

```yaml
name: backend

on:
  push:
    branches: [main]
    paths:
      - "apartment-review-fastapi/**"
      - ".github/workflows/backend.yml"

jobs:
  test:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: apartment-review-fastapi
    steps:
      - uses: actions/checkout@v7
      - uses: astral-sh/setup-uv@v10.3.3
      - run: uv sync --locked
      - run: uv run black --check .
      - run: uv run flake8 .
      - run: uv run pytest
      - run: docker build .
```

What each line is for:

- `paths`: run only when the backend (or this file) changes.
- `setup-uv`: installs uv.
  - Caches `~/.cache/uv` keyed on `uv.lock` by default on GitHub-hosted runners.
  - `uv sync` reads [.python-version](apartment-review-fastapi/.python-version) and downloads Python 3.10 itself. No separate Python setup step.
- `uv sync --locked`: install exactly what `uv.lock` says.
  - **Fails** if `pyproject.toml` and `uv.lock` disagree (review focus 1).
  - The dev group (pytest, black, flake8) is installed by default.
- `docker build .`: the same build DigitalOcean will run.
  - Catches a broken Dockerfile before the deploy job (review focus 5).
  - Adds ~1–2 min.

- [x] ✅ **Step 2: Check the YAML parses locally**
  - Run: `python3 -c "import yaml,sys; yaml.safe_load(open('.github/workflows/backend.yml')); print('ok')"`
  - Expected: `ok`
  - If `yaml` is missing: `uv run --with pyyaml python -c ...`

- [x] ✅ **Step 3: Commit** — `2107b48`, pushed 2026-11-08
  - Message: `add backend CI workflow`

- [x] ✅ **Step 4: Verify on GitHub**
  - GitHub → Actions → `backend` → the run for your push → `test` is green.
  - First run ~3 min (no cache yet).
  - What happened: run 42473923633 failed in 6 s because `setup-uv@v10` does not exist.
  - After the pin to `@v10.3.3` (`08628ba`): runs 42476163103 and 42476589204 green in ~50 s.

---

## ✅ Task 3: Frontend CI workflow

![](https://img.shields.io/badge/TASK_3-DONE-2ea44f?style=for-the-badge) 🟩🟩🟩🟩 **4/4** · commit `91ae7b3` · 2026-11-08

**Files**

- Create: `.github/workflows/frontend.yml`

**Interfaces**

- None downstream.
- Cloudflare Pages builds and deploys `main` on its own; this workflow only reports whether the tests and build pass (decision 4).

- [x] ✅ **Step 1: Write the workflow**

```yaml
name: frontend

on:
  push:
    branches: [main]
    paths:
      - "apartment-review-vue/**"
      - ".github/workflows/frontend.yml"

jobs:
  build:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: apartment-review-vue
    steps:
      - uses: actions/checkout@v7
      - uses: actions/setup-node@v7
        with:
          node-version-file: apartment-review-vue/.nvmrc
          cache: npm
          cache-dependency-path: apartment-review-vue/package-lock.json
      - run: npm ci
      - run: npm test
      - run: npm run build
```

- `npm test` = `vitest run`: runs every `*.spec.ts` under `src/` once (no watch mode); exits 1 on a failing test.
- `npm run build` = `run-p type-check "build-only {@}"` ([package.json](apartment-review-vue/package.json)): `vue-tsc --build` and `vite build` in parallel, so a type error fails the job.

- [x] ✅ **Step 2: Check the YAML parses locally**
  - Run: `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/frontend.yml')); print('ok')"`
  - Expected: `ok`

- [x] ✅ **Step 3: Commit** — `91ae7b3`, pushed 2026-11-08
  - Message: `add frontend CI workflow`

- [x] ✅ **Step 4: Verify on GitHub**
  - The Tasks 1–4 push changed files under `apartment-review-vue/`, so `frontend / build` ran on it.
  - Expected: green, ~1 min.
  - What happened: run 42473923612 green in 22 s on 2026-11-08.

---

## ✅ Task 4: Pulumi: fix the project file, point at the monorepo, let CI trigger backend deploys

![](https://img.shields.io/badge/TASK_4-DONE-2ea44f?style=for-the-badge) 🟩🟩🟩🟩🟩🟩🟩🟩🟩 **9/9** · commit `57898f4` · 2026-11-08

**Files**

- Modify: [Pulumi.yaml](infra/Pulumi.yaml), [Pulumi.dev.yaml](infra/Pulumi.dev.yaml), [index.ts](infra/index.ts)
- Modify: [infra/README.md](infra/README.md), [apartment-review-fastapi/README.md](apartment-review-fastapi/README.md), [apartment-review-vue/README.md](apartment-review-vue/README.md)

**Interfaces**

- Produces a new stack output `backendAppId` (DigitalOcean's generated id for the app).
- Task 5 copies it into the GitHub variable `DO_APP_ID`.
- Task 6's workflow reads that variable.

Which values are ours vs assigned by the outside system:

| Value | Who picks it | Notes |
|---|---|---|
| `sourceDir: "apartment-review-fastapi"` | ours | folder in our repo; DigitalOcean's Docker build context, relative to repo root |
| `dockerfilePath: "apartment-review-fastapi/Dockerfile"` | ours | relative to the **repo root**, not to `sourceDir` (DigitalOcean's rule) |
| `deployOnPush: false` | DigitalOcean flag | off = DigitalOcean no longer watches `main`; CI triggers deploys instead |
| `rootDir: "apartment-review-vue"` | ours | folder Cloudflare runs `npm run build` in; `destinationDir: "dist"` is relative to it |
| `repoName: "apartment-review"` | ours, must match GitHub | the monorepo's name |
| `backendApp.id` → output `backendAppId` | **DigitalOcean-generated** | a UUID-like id; not renameable |

- [x] ✅ **Step 1: Fix the project file so Pulumi can load it**
  - Delete lines 4–8 of `Pulumi.yaml` (the `config:` block).
  - Why: project-level config entries with a provider prefix like `cloudflare:apiToken` need a `value:`, which these never had.
  - The README already sets them with `pulumi config set --secret` into the stack file instead.
  - File becomes:

```yaml
name: apartment-review-infra
runtime: nodejs
description: Cloudflare Pages (frontend) + DigitalOcean App Platform (backend) + Neon (Postgres) for apartment-review
```

- Run: `cd infra && pulumi stack ls`
- Expected: an empty table with the header `NAME  LAST UPDATE  RESOURCE COUNT` (no error).

- [x] ✅ **Step 2: One repo, one branch in the stack config**
  - After the monorepo move, `backendRepo`/`frontendRepo` (and the two branch keys) must always be equal.
  - Keeping both is a mistake waiting to happen, so one key each.
  - `Pulumi.dev.yaml` becomes:

```yaml
config:
  cloudflareAccountId: "REPLACE_WITH_YOUR_CLOUDFLARE_ACCOUNT_ID"
  neonOrgId: "REPLACE_WITH_YOUR_NEON_ORG_ID"
  githubOwner: "tom-leon"
  githubRepo: "apartment-review"
  branch: "main"
  doRegion: "sgp"
  doInstanceSize: "apps-s-1vcpu-0.5gb"
```

- [x] ✅ **Step 3: Same in `index.ts`, lines 12–17**

```ts
// --- repo / branch locations -------------------------------------------------
const githubOwner = cfg.get("githubOwner") ?? "tom-leon";
const githubRepo = cfg.get("githubRepo") ?? "apartment-review";
const branch = cfg.get("branch") ?? "main";
```

- [x] ✅ **Step 4: DigitalOcean service: build from the subfolder, stop auto-deploying**
  - `index.ts`, inside `services: [ { ... } ]`:

```ts
      {
        name: "api",
        github: {
          repo: `${githubOwner}/${githubRepo}`,
          branch,
          deployOnPush: false,
        },
        sourceDir: "apartment-review-fastapi",
        dockerfilePath: "apartment-review-fastapi/Dockerfile",
        httpPort: 8000,
```

- [x] ✅ **Step 5: Cloudflare Pages: build from the subfolder**
  - `index.ts`, the `PagesProject` block:

```ts
const frontendProject = new cloudflare.PagesProject("apartment-review-frontend", {
  accountId: cloudflareAccountId,
  name: pagesProjectName,
  productionBranch: branch,
  buildConfig: {
    buildCommand: "npm run build",
    destinationDir: "dist",
    rootDir: "apartment-review-vue",
  },
  source: {
    type: "github",
    config: {
      owner: githubOwner,
      repoName: githubRepo,
      productionBranch: branch,
      deploymentsEnabled: true,
    },
  },
```

- [x] ✅ **Step 6: Export the app id for CI**
  - `index.ts` outputs:

```ts
export const backendUrl = backendApp.liveUrl;
export const backendAppId = backendApp.id;
export const frontendUrl = frontendProject.domains;
export const databaseConnectionString = databaseUrl;
```

- [x] ✅ **Step 7: Type-check the program**
  - The Neon SDK is generated locally (no npm package), so run the README's install first:

```bash
cd infra
npm install
pulumi package add terraform-provider kislerdm/neon   # writes infra/sdks/neon and adds "@pulumi/neon" to package.json
npm run build                                          # tsc --noEmit
```

- Expected: no TypeScript errors.
- Commit the `sdks/neon/*.ts` source and the `package.json` change.
- The SDK's `node_modules/` and `bin/` are ignored (66 MB of generated files).
- Fresh clone: run `pulumi package add terraform-provider kislerdm/neon` before `npm install`, since `package.json` points at `file:sdks/neon`.

- [x] ✅ **Step 8: Fix the three README sentences that are now false**
  - [infra/README.md:26](infra/README.md#L26): in "grant it access to apartment-review-fastapi", change the repo name to `apartment-review`.
  - [apartment-review-fastapi/README.md:46-47](apartment-review-fastapi/README.md#L46-L47): replace from "the Pulumi stack targets" to the end of the sentence with:

```
the Pulumi stack targets this folder of `tom-leon/apartment-review` (`main` branch), and
GitHub Actions asks DigitalOcean to redeploy after the backend tests pass
(`.github/workflows/backend.yml`).
```

- [apartment-review-vue/README.md:13-14](apartment-review-vue/README.md#L13-L14): replace the two lines with:

```
Cloudflare Pages builds this folder directly (root directory `apartment-review-vue`, `npm run build`,
serving `dist/`). The API (`apartment-review-fastapi/`) is deployed to DigitalOcean from its `Dockerfile`
by GitHub Actions after its tests pass.
```

- [x] ✅ **Step 9: Commit** — `57898f4`, pushed 2026-11-08
  - Message: `point infra at the monorepo and let CI trigger backend deploys`

---

## 🔴 Task 5: First production deploy (manual; each cloud step is a write)

![](https://img.shields.io/badge/TASK_5-NOT_STARTED-d73a49?style=for-the-badge) ⬜⬜⬜⬜⬜⬜ **0/6** · run by hand from `infra/`

> [!CAUTION]
> **Manual only.**
> - Nothing exists yet in Pulumi Cloud, DigitalOcean, Cloudflare or Neon for this project.
> - Every step below creates or changes something in a cloud account.
> - Each one is a deliberate manual action. None of it is automated from this plan.

**Produces**

- A live backend URL.
- A live frontend URL.
- A Neon database.
- The secret `DIGITALOCEAN_ACCESS_TOKEN` and the variable `DO_APP_ID`. These two unblock Task 6.

**Prerequisites: where the five config values come from** (dashboards, once; not steps, nothing is created yet)

- Neon has no GitHub app to authorise. Pulumi creates the project and database through its API, so Neon only needs these two values:
  - **Neon org id:** console → switch to the organisation → Settings → General information → *Organization ID* (`org-…`).
  - **Neon API key:** console → Account settings → API keys → Create → copy it now (shown once). An organisation key (Organization → Settings → API keys) also works; admins only.
- **Cloudflare account id:** dashboard → Workers & Pages → overview → Account details → copy *Account ID*.
- **Cloudflare API token:** My Profile → API Tokens → Create Token → Custom token → permissions `Account · Cloudflare Pages · Edit` and `Account · Account Settings · Read` → Account resources: your account → copy it now (shown once).
- **DigitalOcean token for Pulumi:** API → Tokens → Generate New Token → Full Access → copy it now (shown once). The narrower CI token is a separate token, made in step 5.

- [ ] 🔲 **Step 1: Create the stack and set the config** (from `infra`)

```bash
pulumi stack init dev
pulumi config set cloudflareAccountId <cloudflare account id>
pulumi config set neonOrgId <neon org id>
pulumi config set --secret digitalocean:token <DigitalOcean token, full read/write — Pulumi creates the app>
pulumi config set --secret cloudflare:apiToken <Cloudflare token: Cloudflare Pages:Edit + Account Settings:Read>
pulumi config set --secret neonApiKey <Neon API key>
```

- [ ] 🔲 **Step 2: Authorise the two GitHub apps on the monorepo** (dashboard, once)
  - DigitalOcean: Apps → Create App → GitHub → authorise → grant access to `tom-leon/apartment-review` → cancel the wizard.
  - Cloudflare: Workers & Pages → Create → Pages → Connect to Git → authorise the same repo → cancel.

- [ ] 🔲 **Step 3: Preview, then create everything**

```bash
pulumi preview   # expect 6 to create: stack, Neon provider, Neon project, Neon database, DigitalOcean app, Cloudflare Pages project
pulumi up
```

- Creating the app starts its first deployment even with `deployOnPush: false`.
- Creating the Pages project with a Git source starts its first build. If it doesn't, push any commit to `main`.

- [ ] 🔲 **Step 4: Smoke-test**

```bash
curl -s "$(pulumi stack output backendUrl)/"
```

- Expected: `{"status":"healthy","message":"API is running"}` (the `/` route in [main.py](apartment-review-fastapi/main.py)).
- Then open `pulumi stack output frontendUrl` in a browser: the Vue app renders.
- CORS and the API base URL are wired now. The list route itself is still missing (see *Found while planning*).

- [ ] 🔲 **Step 5: Give CI a narrowly scoped DigitalOcean token**
  - DigitalOcean → API → Generate New Token → Custom Scopes → `app:read` + `app:update`.
  - Those are what "create deployment" and `--wait` polling need. Scopes can't be edited after creation.
  - Then:

```bash
gh secret set DIGITALOCEAN_ACCESS_TOKEN -R tom-leon/apartment-review          # paste the token
gh variable set DO_APP_ID -R tom-leon/apartment-review --body "$(pulumi stack output backendAppId)"
```

- [ ] 🔲 **Step 6 (optional): stop Cloudflare rebuilding on backend-only pushes**
  - Cloudflare dashboard → the Pages project → Settings → Build → Build watch paths → Include `apartment-review-vue/*`.
  - Not settable from the Pulumi v5 provider.
  - Saves builds against the 500/month free quota. Harmless to skip.

🔒 **Task 6 stays blocked until step 5 here is done.**

---

## 🔒 Task 6: Backend deploy job

![](https://img.shields.io/badge/TASK_6-BLOCKED-8b949e?style=for-the-badge) ⬜⬜⬜⬜ **0/4** · blocked until Task 5 step 5

> [!WARNING]
> Do not add this job before the secret and variable exist, or every push to `main` goes red (review focus 6).

**Files**

- Modify: `.github/workflows/backend.yml` (from Task 2)

**Interfaces**

- Consumes job `test` (Task 2).
- Consumes secret `DIGITALOCEAN_ACCESS_TOKEN` and variable `DO_APP_ID` (Task 5).

- [ ] 🔲 **Step 1: Add the deploy job** at the end of `jobs:` in `backend.yml`

```yaml
  deploy:
    needs: test
    runs-on: ubuntu-latest
    concurrency: backend-production
    steps:
      - uses: digitalocean/action-doctl@v2
        with:
          token: ${{ secrets.DIGITALOCEAN_ACCESS_TOKEN }}
      - run: doctl apps create-deployment ${{ vars.DO_APP_ID }} --wait
```

- `concurrency: backend-production`: a second push waits for the first deploy to finish instead of racing it (review focus 2).
- No `checkout` and no `working-directory`: the job only talks to DigitalOcean (review focus 4).
- `create-deployment`: tells DigitalOcean to rebuild from the current head of `main`.
- `--wait`: the job fails if the deployment fails, so a bad deploy shows up red in Actions.

- [ ] 🔲 **Step 2: Check the YAML parses locally**
  - Run: `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/backend.yml')); print('ok')"`
  - Expected: `ok`

- [ ] 🔲 **Step 3: Commit and push to `main`**
  - Message: `deploy backend from CI after tests pass`

- [ ] 🔲 **Step 4: Verify end to end**
  - The push changes `backend.yml`, so the workflow runs.
  - Actions → `backend` → `test` green, then `deploy` green with `doctl` printing the deployment reaching `ACTIVE`.
  - DigitalOcean → the app → Deployments shows a new deployment whose source is the API, not a Git push.
  - Re-run the Task 5 `curl`.

**Rollback, if ever needed**

- DigitalOcean → Deployments → pick the previous one → Rollback.
- Cloudflare → the Pages project → Deployments → previous → Rollback to this deployment.

---

## 🔵 Task 7: Dependabot

![](https://img.shields.io/badge/TASK_7-READY-0969da?style=for-the-badge) ⬜⬜⬜⬜⬜⬜ **0/6** · can be done any time after Task 3

- Dependabot is GitHub's free bot. It opens a pull request whenever a dependency has a new version or a security fix.
- It only works through PRs, so this is the one place PRs come back.
- Dependabot opens one, CI tests it, you merge it or close it.

**Files**

- Create: `.github/dependabot.yml`
- Modify: `.github/workflows/backend.yml`, `.github/workflows/frontend.yml` (from Tasks 2, 3, 6)

**Interfaces**

- The workflows must also run on `pull_request` so Dependabot's PRs get tested.
- The backend `deploy` job must not run on those PRs.

- [ ] 🔲 **Step 1: Write the Dependabot config**

```yaml
version: 2
updates:
  - package-ecosystem: npm
    directory: /apartment-review-vue
    schedule:
      interval: weekly
  - package-ecosystem: uv
    directory: /apartment-review-fastapi
    schedule:
      interval: weekly
  - package-ecosystem: github-actions
    directory: /
    schedule:
      interval: weekly
```

- The third entry bumps the `@v7`/`@v10.3.3` pins in the workflows themselves.
- Weekly keeps it to one batch of PRs on a Monday rather than a trickle.

- [ ] 🔲 **Step 2: Let both workflows run on pull requests too**
  - In both `backend.yml` and `frontend.yml`, the `on:` block becomes (same `paths` as before):

```yaml
on:
  push:
    branches: [main]
    paths:
      - "apartment-review-fastapi/**"
      - ".github/workflows/backend.yml"
  pull_request:
    paths:
      - "apartment-review-fastapi/**"
      - ".github/workflows/backend.yml"
```

- Frontend: the `apartment-review-vue/**` and `frontend.yml` paths.

- [ ] 🔲 **Step 3: Keep the deploy job off PRs**
  - In `backend.yml`, add one line to the `deploy` job so it only runs for pushes to `main`, never for a PR:

```yaml
  deploy:
    needs: test
    if: github.event_name == 'push'
    runs-on: ubuntu-latest
```

- Dependabot PR runs also don't get repository secrets. Without this line the deploy step would fail on every bump anyway.

- [ ] 🔲 **Step 4: Check the YAML parses**
  - Run: `for f in .github/dependabot.yml .github/workflows/*.yml; do python3 -c "import yaml,sys; yaml.safe_load(open('$f'))" && echo "ok $f"; done`
  - Expected: `ok` three times.

- [ ] 🔲 **Step 5: Commit and push to `main`**
  - Message: `add dependabot for npm, uv and github actions`

- [ ] 🔲 **Step 6: Verify**
  - GitHub → Insights → Dependency graph → Dependabot shows the three ecosystems with "last checked" times.
  - Within a day the first PRs appear; each one shows the `backend` or `frontend` check.
  - Merge a green one with `gh pr merge <number> --squash --delete-branch`.
  - The resulting push to `main` runs the deploy job as normal.

---

## Found while planning, not in this plan

✅ = done since · 🔲 = still open.

- 🔲 **The Dockerfile ignores `uv.lock`.**
  - It runs `uv pip install --system -e .`, which resolves fresh from `pyproject.toml`.
  - So DigitalOcean can install different versions from the ones CI tested.
  - It also breaks the repo's own "never `uv pip`" rule.
  - Fix: `uv sync --locked --no-dev` and `CMD ["uv", "run", "uvicorn", ...]`.
  - Worth doing right after this plan. It is what would push us towards option C otherwise.
- ✅ **CORS middleware** — done 2026-11-08 (`ce61742`).
  - `CORS_ORIGINS` env var, allowed origins only, never `*`.
  - Pulumi sets it on the DigitalOcean app to the Pages domain.
- ✅ **Frontend reads `VITE_API_URL`** — done 2026-11-08 (`d424bee`).
  - The store builds every request from it.
  - `.env.development` sets it for `npm run dev`.
- 🔲 **The list route still doesn't exist.**
  - [apartment.ts](apartment-review-vue/src/stores/apartment.ts) calls `/api/apartments`; the backend serves `/user`, `/apartment`, `/`.
  - Owned by the features plan. The Task 5 smoke test only covers `/`.
- 🔲 **Neon connection string likely points at the wrong database.**
  - `neonProject.connectionUri` is the project's *default* database (`neondb`).
  - The program also creates `apartment_review`; tables will land in `neondb` on first start.
  - Unverified until the first deploy. Check which database has tables.
- 🔲 **Postgres 18 locally, 16 on Neon** ([docker-compose.yml](apartment-review-vue/docker-compose.yml) vs [index.ts](infra/index.ts) `pgVersion: 16`).
- 🔲 **`deploymentsEnabled` is deprecated** in the Cloudflare provider.
  - `productionDeploymentEnabled` + `previewDeploymentSetting` replace it.
  - Left untouched because it still works.
- 🔲 **The two old repos** (`apartment-review-fastapi`, `apartment-review-vue`) are still live on GitHub.
  - Archiving them avoids authorising the wrong one in Task 5.
- 🔲 [DOCKER_GUIDE.md](apartment-review-vue/DOCKER_GUIDE.md) still lists the old ports (the README already notes this).

---

*Legend:* 🟩 step done · ⬜ step open · ✅ done · 🔲 to do · 🔴 not started · 🔒 blocked · 🔵 ready. Update the progress block, the task badge and the bar every time a step flips.
