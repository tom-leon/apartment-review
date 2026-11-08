# CI/CD plan — apartment-review (Vue + FastAPI)

**Goal:** every push to `main` runs the backend tests and the frontend tests + build automatically, and puts the backend live only after its tests pass, while Cloudflare builds and publishes the frontend from `main` itself. Single contributor, no pull requests: `main` is the only branch.

**Architecture:** two small GitHub Actions workflows (one per app, each only runs when its folder changes). The backend workflow runs lint + tests + a Docker build, then asks DigitalOcean to redeploy. The frontend workflow runs the Vitest tests and the build; Cloudflare Pages builds and deploys `main` on its own with the same build command. The existing Pulumi program is fixed so it can run, pointed at the monorepo, and told to let CI trigger backend deploys.

**Tech stack:** GitHub Actions · uv + pytest + black + flake8 · npm + vue-tsc + Vite · Docker · Pulumi (TypeScript) · DigitalOcean App Platform · Cloudflare Pages · Neon Postgres.

**Spec:** the *Why*, *What's true today* and *Design* sections of this file.

---

## Why

Right now nothing checks a change after it lands on `main`, and nothing is deployed anywhere, so there's no way to put the app in front of a person. The cost of staying here: a broken commit is found by hand, days later, and "deploy" is a manual afternoon that has never actually been done. After this plan: a red check on `main` tells you within ~3 minutes that you broke tests, formatting or the Docker image; a push to `main` ships the backend by itself and only if green; the frontend ships itself on every `main` build; and production exists.

## What's true today (checked 2026-10-13)

| Area | Fact | Evidence |
|---|---|---|
| CI | No workflows anywhere; GitHub Actions is enabled on the repo | no `.github/` folder; `gh api repos/.../actions/permissions` → `enabled: true` |
| Repo | Private, on GitHub Free. **Branch protection and rulesets are not available** (403 "Upgrade to GitHub Pro or make this repository public") | `gh api .../branches/main/protection` |
| Backend tests | 4 pass, using an in-memory SQLite database, so **CI needs no Postgres** | `uv run pytest` ([conftest.py](apartment-review-fastapi/tests/conftest.py)) |
| Backend lint | `black --check` fails (6 files, formatting only, ~330 diff lines). `flake8` with a black-compatible config leaves 10 real issues after black: 8 unused imports, 2 long lines. There is no flake8 config, so today it also scans `.venv` and reports 28,000 "errors" | `uv run black --check .`, `uv run flake8 .` |
| Backend lockfile | `uv.lock` is in sync with `pyproject.toml` | `uv lock --check` → ok |
| Backend Docker | [Dockerfile](apartment-review-fastapi/Dockerfile) builds | `docker build .` → exit 0 |
| Frontend | `npm ci`, `npm test` (Vitest, 2 tests) and `npm run build` (type-check + Vite build) pass on Node 22. **No lint exists** | [package.json](apartment-review-vue/package.json) |
| Infra | The Pulumi project file is malformed, so Pulumi can't even load it. With the bad block removed, it loads and shows **no stacks: nothing has ever been deployed** | `pulumi stack ls` → "Configuration key 'cloudflare:apiToken' is namespaced and must provide an attribute 'value'" ([Pulumi.yaml:4-8](infra/Pulumi.yaml#L4-L8)) |
| Infra | The program still names the two pre-monorepo repos (`apartment-review-fastapi`, `apartment-review-vue`), which still exist on GitHub, unarchived, last pushed 2026-02-06 | [index.ts:14-17](infra/index.ts#L14-L17) |
| GitHub account | Renamed from `yilin-chao` to `tom-leon` (checked 2026-11-08). Old URLs redirect, so `git push` still works, but DigitalOcean, Cloudflare and Pulumi must use `tom-leon` | `gh api user` → `tom-leon`; `gh repo view yilin-chao/apartment-review` → url `tom-leon/apartment-review` |

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

Terms used above, once: **CI** = the checks that run on every change. **CD** = the step that puts a change live. **Workflow** = one YAML file that GitHub Actions runs. **`doctl`** = DigitalOcean's command-line tool. **App Platform** = DigitalOcean's "give it a Dockerfile and it runs it" service. **Cloudflare Pages** = a static-site host that builds straight from a Git repo.

### Options considered

| | A. Platforms auto-deploy, Actions only reports | **B. Actions gates the backend deploy (this plan)** | C. Build once, deploy the exact artifact |
|---|---|---|---|
| Backend goes live by | DigitalOcean watches `main` | Actions, after tests pass, runs `doctl apps create-deployment` | Actions builds the image → DigitalOcean Container Registry → app runs that image |
| Frontend goes live by | Cloudflare watches `main` | Cloudflare watches `main` (its build *is* our only frontend check) | Actions runs `wrangler pages deploy dist` |
| Secrets to put in GitHub | 0 | 1 token + 1 app id | DigitalOcean token, Cloudflare token, registry login |
| Bad backend commit pushed | goes live | **blocked** | **blocked** |
| Tested == deployed? | no | same commit, rebuilt by DigitalOcean | exactly the tested image |
| Extra code | none | ~10 lines of YAML | ~60 lines of YAML + Pulumi rewrite (image source, direct-upload Pages) |

**Recommendation: B.** It is the smallest change that makes tests actually gate a deploy. A doesn't gate anything. C's extra guarantee (ship the exact image CI tested) only matters once the Docker build isn't reproducible, and it costs a Pulumi rewrite. Move to C later if a DigitalOcean build ever differs from CI (see the Dockerfile note under *Found while planning*).

### Decisions you can still flip

1. **Approach B** over A or C (above).
2. **Lint in CI.** `black` and `flake8` are already dev dependencies, so the plan runs them and Task 1 makes them pass (10 one-line fixes + a black reformat). To skip: drop Task 1 and the two lint lines in Task 2.
3. **Frontend checks.** Vitest is now installed with one store test, so CI runs `npm test` then `npm run build`. ESLint and Prettier are still not installed; adding them is its own decision.
4. **Frontend tests don't gate the frontend deploy.** Cloudflare deploys `main` as soon as its own build passes; a failing Vitest test only shows red in Actions. To gate it too: set `productionDeploymentEnabled: false` in Pulumi, create a Cloudflare deploy hook (a secret URL that starts a build when POSTed), and add a `deploy` job to `frontend.yml` that `curl -X POST`s it after tests. About 8 lines plus one more secret. Not in this plan; say if you want it.

## Global constraints

- Python **3.10** everywhere: [.python-version](apartment-review-fastapi/.python-version), [Dockerfile](apartment-review-fastapi/Dockerfile) `python:3.10-slim`. Dependencies via **uv** only; never `uv pip` ([CLAUDE.md](apartment-review-fastapi/CLAUDE.md)).
- Node **22**: [.nvmrc](apartment-review-vue/.nvmrc), `engines >=22.12.0`. Install with `npm ci` (uses `package-lock.json` exactly).
- Action versions as of 2026-11-08: `actions/checkout@v7`, `actions/setup-node@v7`, `astral-sh/setup-uv@v10.3.3`, `digitalocean/action-doctl@v2`. setup-uv publishes **no floating `v10` tag** (the first run failed with "unable to find version `v10`"), so it is pinned to the full version and Dependabot (Task 7) will bump it. `action-doctl@v2` is a *branch*, not a tag, and resolves fine.
- Pulumi provider versions stay as pinned in [infra/package.json](infra/package.json). Cloudflare provider v5 has `buildConfig.rootDir` but **no** build-watch-path fields, so that stays a dashboard setting.
- Australian English in code and docs.
- Git: single contributor, no PRs, everything goes straight to `main`. One-line commit messages, no `feat:` prefix.
- Cloud: every create/change in DigitalOcean, Cloudflare, Neon or Pulumi Cloud is a deliberate manual step, never automated from a plan. Task 5 is run by hand.

## Review focus

Things the design implies but no unit test covers. Each is pinned by a step in the task named.

1. `pyproject.toml` edited without re-locking → CI must **fail**, not quietly install something else. Pinned by `uv sync --locked` (Task 2).
2. Two pushes to `main` minutes apart → the second deploy must **queue**, not race or cancel the first. Pinned by `concurrency: backend-production` on the deploy job (Task 6).
3. A push that changes only a workflow file → that workflow must still run. Pinned by listing the workflow file in its own `paths` (Tasks 2, 3).
4. The deploy job never checks out the repo → a job-wide `working-directory` would fail with "no such directory". Pinned by scoping `defaults.run.working-directory` to the `test` job only (Tasks 2, 6).
6. A `deploy` job that exists before its secrets do → every push to `main` goes red. Pinned by the task order: Task 6 is added only after Task 5 has set the secret and variable.
7. A Dependabot PR triggers the backend workflow → the `deploy` job must not run (no secrets on PR runs, and nothing should ship from a PR). Pinned by `if: github.event_name == 'push'` (Task 7).
5. Backend Dockerfile breaks → must fail in Actions before the deploy job runs, not on DigitalOcean. Pinned by `docker build .` in the test job (Task 2).

## How to run this plan

Tasks 1–4 are committed and pushed to `main` together. That push touches both app folders, so it is itself the proof that Tasks 2 and 3 work. Then Task 5 (first deploy) is run by hand. Then Task 6 is one more commit to `main`, verified by that push. Task 7 (Dependabot) can go any time after Task 3.

---

### Task 1: Make black and flake8 pass (backend)

**Files:**
- Create: `apartment-review-fastapi/.flake8`
- Modify: [database.py](apartment-review-fastapi/database.py), [example_endpoints.py](apartment-review-fastapi/example_endpoints.py), [schemas.py](apartment-review-fastapi/schemas.py), [utils.py](apartment-review-fastapi/utils.py) (by hand), plus whatever `black` reformats ([main.py](apartment-review-fastapi/main.py), [models.py](apartment-review-fastapi/models.py) and the four above)

**Interfaces:** produces a backend where `uv run black --check .`, `uv run flake8 .` and `uv run pytest` all exit 0. Task 2 relies on that.

- [x] **Step 1: Add the flake8 config** (black uses 88-column lines; flake8 defaults to 79 and scans `.venv`)

Create `apartment-review-fastapi/.flake8`:

```ini
[flake8]
max-line-length = 88
extend-ignore = E203,W503
exclude = .venv
```

`E203`/`W503` are the two rules black deliberately breaks (whitespace before `:` in slices, line breaks before operators).

- [x] **Step 2: Let black reformat**

Run: `cd apartment-review-fastapi && uv run black .`
Expected: `6 files reformatted, 3 files left unchanged.` Formatting only; nothing behavioural.

- [x] **Step 3: See what flake8 still wants**

Run: `uv run flake8 .`
Expected exactly these 10 (line numbers are after black):

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

(`example_endpoints.py` is not imported by anything, so removing its unused imports changes nothing at runtime.)

- [x] **Step 4: Remove the 8 unused imports**

`database.py` — delete line 3:

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel          # ← delete this line

from config import database_url
```

`example_endpoints.py` — the import block becomes:

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

(removed: `from datetime import datetime`; `Apartment, User` from the models line; `ApartmentCreate,`; `calculate_apartment_average_rating,`)

`schemas.py` line 1:

```python
from pydantic import BaseModel, Field
```

`utils.py` line 4:

```python
from schemas import OSMAddressData
```

- [x] **Step 5: Wrap the 2 long lines**

`example_endpoints.py`, inside `create_review` (the only `HTTP_409_CONFLICT` in the file):

```python
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You have already reviewed this apartment. "
            "Use PUT to update your review.",
        )
```

`utils.py`, the `get_or_create_apartment` docstring:

```python
    Returns:
        Tuple of (Apartment, created) where created is True if a new apartment
        was created
    """
```

- [x] **Step 6: Verify all three are green**

Run: `uv run black --check . && uv run flake8 . && uv run pytest -q`
Expected: `All done!`, no flake8 output, `4 passed`. If black wants to re-wrap the two edited lines, run `uv run black .` once more and re-run the check.

- [x] **Step 7: Commit** — `6ae894a`, pushed 2026-11-08

Message: `make black and flake8 pass`

---

### Task 2: Backend CI workflow

**Files:**
- Create: `.github/workflows/backend.yml`

**Interfaces:** produces a job named `test` that Task 6's `deploy` job will depend on via `needs: test`. The job name must stay `test`.

- [x] **Step 1: Write the workflow**

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
- `paths` — run only when the backend (or this file) changes.
- `setup-uv` — installs uv; on GitHub-hosted runners it caches `~/.cache/uv` keyed on `uv.lock` by default. `uv sync` then reads [.python-version](apartment-review-fastapi/.python-version) and downloads Python 3.10 itself, so no separate Python setup step.
- `uv sync --locked` — install exactly what `uv.lock` says, and **fail** if `pyproject.toml` and `uv.lock` disagree (review focus 1). The dev group (pytest, black, flake8) is installed by default.
- `docker build .` — the same build DigitalOcean will run; catches a broken Dockerfile before the deploy job (review focus 5). Adds ~1–2 min.

- [x] **Step 2: Check the YAML parses locally**

Run: `python3 -c "import yaml,sys; yaml.safe_load(open('.github/workflows/backend.yml')); print('ok')"`
Expected: `ok` (if `yaml` is missing: `uv run --with pyyaml python -c ...`).

- [x] **Step 3: Commit** — `2107b48`, pushed 2026-11-08

Message: `add backend CI workflow`

- [ ] **Step 4: Verify on GitHub (after Tasks 1–4 are pushed to `main`)** — first run 42473923633 failed in 6 s: `setup-uv@v10` does not exist. Fixed to `@v10.3.3` in the working tree; re-verify after that is pushed.

GitHub → Actions → `backend` → the run for your push → `test` is green. First run ~3 min (no cache yet).

---

### Task 3: Frontend CI workflow

**Files:**
- Create: `.github/workflows/frontend.yml`

**Interfaces:** none downstream. Cloudflare Pages builds and deploys `main` on its own; this workflow only reports whether the tests and build pass (decision 4).

- [x] **Step 1: Write the workflow**

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

`npm test` is `vitest run`: executes every `*.spec.ts` under `src/` once (no watch mode) and exits 1 on a failing test. `npm run build` is `run-p type-check "build-only {@}"` in [package.json](apartment-review-vue/package.json): `vue-tsc --build` and `vite build` in parallel, so a type error fails the job.

- [x] **Step 2: Check the YAML parses locally**

Run: `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/frontend.yml')); print('ok')"`
Expected: `ok`

- [x] **Step 3: Commit** — `91ae7b3`, pushed 2026-11-08

Message: `add frontend CI workflow`

- [x] **Step 4: Verify on GitHub** — run 42473923612 green in 22 s on 2026-11-08

The Tasks 1–4 push changes files under `apartment-review-vue/`, so `frontend / build` runs on it. Expected: green, ~1 min.

---

### Task 4: Pulumi: fix the project file, point at the monorepo, let CI trigger backend deploys

**Files:**
- Modify: [Pulumi.yaml](infra/Pulumi.yaml), [Pulumi.dev.yaml](infra/Pulumi.dev.yaml), [index.ts](infra/index.ts), [infra/README.md](infra/README.md), [apartment-review-fastapi/README.md](apartment-review-fastapi/README.md), [apartment-review-vue/README.md](apartment-review-vue/README.md)

**Interfaces:** produces a new stack output `backendAppId` (DigitalOcean's generated id for the app). Task 5 copies it into the GitHub variable `DO_APP_ID`, which Task 6's workflow reads.

Which values are ours vs assigned by the outside system:

| Value | Who picks it | Notes |
|---|---|---|
| `sourceDir: "apartment-review-fastapi"` | ours | folder in our repo; DigitalOcean's Docker build context, relative to repo root |
| `dockerfilePath: "apartment-review-fastapi/Dockerfile"` | ours | relative to the **repo root**, not to `sourceDir` (DigitalOcean's rule) |
| `deployOnPush: false` | DigitalOcean flag | off = DigitalOcean no longer watches `main`; CI triggers deploys instead |
| `rootDir: "apartment-review-vue"` | ours | folder Cloudflare runs `npm run build` in; `destinationDir: "dist"` is relative to it |
| `repoName: "apartment-review"` | ours, must match GitHub | the monorepo's name |
| `backendApp.id` → output `backendAppId` | **DigitalOcean-generated** | a UUID-like id; not renameable |

- [x] **Step 1: Fix the project file so Pulumi can load it**

Delete lines 4–8 of `Pulumi.yaml` (the `config:` block). Project-level config entries with a provider prefix like `cloudflare:apiToken` need a `value:`, which these never had, and the README already sets them with `pulumi config set --secret` into the stack file instead. File becomes:

```yaml
name: apartment-review-infra
runtime: nodejs
description: Cloudflare Pages (frontend) + DigitalOcean App Platform (backend) + Neon (Postgres) for apartment-review
```

Run: `cd infra && pulumi stack ls`
Expected: an empty table with the header `NAME  LAST UPDATE  RESOURCE COUNT` (no error).

- [x] **Step 2: One repo, one branch in the stack config**

After the monorepo move, `backendRepo`/`frontendRepo` (and the two branch keys) must always be equal, so keeping both is a mistake waiting to happen. `Pulumi.dev.yaml` becomes:

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

- [x] **Step 3: Same in `index.ts`, lines 12–17**

```ts
// --- repo / branch locations -------------------------------------------------
const githubOwner = cfg.get("githubOwner") ?? "tom-leon";
const githubRepo = cfg.get("githubRepo") ?? "apartment-review";
const branch = cfg.get("branch") ?? "main";
```

- [x] **Step 4: DigitalOcean service: build from the subfolder, stop auto-deploying**

`index.ts`, inside `services: [ { ... } ]` (currently lines 76–83):

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

- [x] **Step 5: Cloudflare Pages: build from the subfolder**

`index.ts`, the `PagesProject` block (currently lines 108–124):

```ts
const frontendProject = new cloudflare.PagesProject("apartment-review-frontend", {
  accountId: cloudflareAccountId,
  name: "apartment-review",
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

- [x] **Step 6: Export the app id for CI**

`index.ts` outputs (currently lines 139–141):

```ts
export const backendUrl = backendApp.liveUrl;
export const backendAppId = backendApp.id;
export const frontendUrl = frontendProject.domains;
export const databaseConnectionString = databaseUrl;
```

- [x] **Step 7: Type-check the program**

The Neon SDK is generated locally (no npm package), so run the README's install first:

```bash
cd infra
npm install
pulumi package add terraform-provider kislerdm/neon   # writes infra/sdks/neon and adds "@pulumi/neon" to package.json
npm run build                                          # tsc --noEmit
```

Expected: no TypeScript errors. Commit the `sdks/neon/*.ts` source and the `package.json` change (the SDK's `node_modules/` and `bin/` are ignored; 66 MB of generated files). On a fresh clone run `pulumi package add terraform-provider kislerdm/neon` before `npm install`, since `package.json` points at `file:sdks/neon`.

- [x] **Step 8: Fix the three README sentences that are now false**

[infra/README.md:26](infra/README.md#L26): in "grant it access to apartment-review-fastapi", change the repo name to `apartment-review`.

[apartment-review-fastapi/README.md:46-47](apartment-review-fastapi/README.md#L46-L47), replace from "the Pulumi stack targets" to the end of the sentence with:

```
the Pulumi stack targets this folder of `tom-leon/apartment-review` (`main` branch), and
GitHub Actions asks DigitalOcean to redeploy after the backend tests pass
(`.github/workflows/backend.yml`).
```

[apartment-review-vue/README.md:13-14](apartment-review-vue/README.md#L13-L14), replace the two lines with:

```
Cloudflare Pages builds this folder directly (root directory `apartment-review-vue`, `npm run build`,
serving `dist/`). The API (`apartment-review-fastapi/`) is deployed to DigitalOcean from its `Dockerfile`
by GitHub Actions after its tests pass.
```

- [x] **Step 9: Commit** — `57898f4`, pushed 2026-11-08

Message: `point infra at the monorepo and let CI trigger backend deploys`

---

### Task 5: First production deploy (run by hand; each cloud step is a write)

Nothing exists yet in Pulumi Cloud, DigitalOcean, Cloudflare or Neon for this project. This is the one-time runbook; the agent does not run these.

- [ ] **Step 1: Create the stack and set the config** (from `infra`)

```bash
pulumi stack init dev
pulumi config set cloudflareAccountId <cloudflare account id>
pulumi config set neonOrgId <neon org id>
pulumi config set --secret digitalocean:token <DigitalOcean token, full read/write — Pulumi creates the app>
pulumi config set --secret cloudflare:apiToken <Cloudflare token: Cloudflare Pages:Edit + Account Settings:Read>
pulumi config set --secret neonApiKey <Neon API key>
```

- [ ] **Step 2: Authorise the two GitHub apps on the monorepo** (dashboard, once)

DigitalOcean: Apps → Create App → GitHub → authorise → grant access to `tom-leon/apartment-review` → cancel the wizard. Cloudflare: Workers & Pages → Create → Pages → Connect to Git → authorise the same repo → cancel.

- [ ] **Step 3: Preview, then create everything**

```bash
pulumi preview   # expect 6 to create: stack, Neon provider, Neon project, Neon database, DigitalOcean app, Cloudflare Pages project
pulumi up
```

Creating the app starts its first deployment even with `deployOnPush: false`. Creating the Pages project with a Git source starts its first build; if it doesn't, push any commit to `main`.

- [ ] **Step 4: Smoke-test**

```bash
curl -s "$(pulumi stack output backendUrl)/"
```

Expected: `{"status":"healthy","message":"API is running"}` (the `/` route in [main.py](apartment-review-fastapi/main.py)). Then open `pulumi stack output frontendUrl` in a browser: the Vue app renders. (It can't talk to the API yet — see *Found while planning*.)

- [ ] **Step 5: Give CI a narrowly scoped DigitalOcean token**

DigitalOcean → API → Generate New Token → Custom Scopes → `app:read` + `app:update` (what "create deployment" and `--wait` polling need; scopes can't be edited after creation). Then:

```bash
gh secret set DIGITALOCEAN_ACCESS_TOKEN -R tom-leon/apartment-review          # paste the token
gh variable set DO_APP_ID -R tom-leon/apartment-review --body "$(pulumi stack output backendAppId)"
```

- [ ] **Step 6 (optional): stop Cloudflare rebuilding on backend-only pushes**

Cloudflare dashboard → the Pages project → Settings → Build → Build watch paths → Include `apartment-review-vue/*`. Not settable from the Pulumi v5 provider. Saves builds against the 500/month free quota; harmless to skip.

---

### Task 6: Backend deploy job

**Files:**
- Modify: `.github/workflows/backend.yml` (from Task 2)

**Interfaces:** consumes job `test` (Task 2), secret `DIGITALOCEAN_ACCESS_TOKEN` and variable `DO_APP_ID` (Task 5).

- [ ] **Step 1: Add the deploy job** at the end of `jobs:` in `backend.yml`

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

- `concurrency: backend-production` — a second push waits for the first deploy to finish instead of racing it (review focus 2).
- No `checkout` and no `working-directory` here: the job only talks to DigitalOcean (review focus 4).
- `create-deployment` tells DigitalOcean to rebuild from the current head of `main`; `--wait` makes the job fail if the deployment fails, so a bad deploy shows up red in Actions.

- [ ] **Step 2: Check the YAML parses locally**

Run: `python3 -c "import yaml; yaml.safe_load(open('.github/workflows/backend.yml')); print('ok')"`
Expected: `ok`

- [ ] **Step 3: Commit and push to `main`**

Message: `deploy backend from CI after tests pass`

- [ ] **Step 4: Verify end to end**

The push changes `backend.yml`, so the workflow runs. Actions → `backend` → `test` green, then `deploy` green with `doctl` printing the deployment reaching `ACTIVE`. DigitalOcean → the app → Deployments shows a new deployment whose source is the API, not a Git push. Re-run the Task 5 `curl`.

Rollback, if ever needed: DigitalOcean → Deployments → pick the previous one → Rollback. Cloudflare → the Pages project → Deployments → previous → Rollback to this deployment.

---

### Task 7: Dependabot

Dependabot is GitHub's free bot that opens a pull request whenever one of your dependencies has a new version or a security fix. It only works through PRs, so this is the one place PRs come back: Dependabot opens one, CI tests it, you merge it or close it.

**Files:**
- Create: `.github/dependabot.yml`
- Modify: `.github/workflows/backend.yml`, `.github/workflows/frontend.yml` (from Tasks 2, 3, 6)

**Interfaces:** the workflows must also run on `pull_request` so Dependabot's PRs get tested, and the backend `deploy` job must not run on those PRs.

- [ ] **Step 1: Write the Dependabot config**

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

The third entry bumps the `@v7`/`@v10` pins in the workflows themselves. Weekly keeps it to one batch of PRs on a Monday rather than a trickle.

- [ ] **Step 2: Let both workflows run on pull requests too**

In both `backend.yml` and `frontend.yml`, the `on:` block becomes (same `paths` as before):

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

(frontend: the `apartment-review-vue/**` and `frontend.yml` paths.)

- [ ] **Step 3: Keep the deploy job off PRs**

In `backend.yml`, add one line to the `deploy` job so it only runs for pushes to `main`, never for a PR:

```yaml
  deploy:
    needs: test
    if: github.event_name == 'push'
    runs-on: ubuntu-latest
```

Dependabot PR runs also don't get repository secrets, so without this line the deploy step would fail on every bump anyway.

- [ ] **Step 4: Check the YAML parses**

Run: `for f in .github/dependabot.yml .github/workflows/*.yml; do python3 -c "import yaml,sys; yaml.safe_load(open('$f'))" && echo "ok $f"; done`
Expected: `ok` three times.

- [ ] **Step 5: Commit and push to `main`**

Message: `add dependabot for npm, uv and github actions`

- [ ] **Step 6: Verify**

GitHub → Insights → Dependency graph → Dependabot shows the three ecosystems with "last checked" times. Within a day the first PRs appear; each one shows the `backend` or `frontend` check. Merge a green one with `gh pr merge <number> --squash --delete-branch`; the resulting push to `main` runs the deploy job as normal.

---

## Found while planning, not in this plan

One line each; say if you want any of them picked up.

- **The Dockerfile ignores `uv.lock`.** It runs `uv pip install --system -e .`, which resolves fresh from `pyproject.toml`, so DigitalOcean can install different versions from the ones CI tested; it also breaks the repo's own "never `uv pip`" rule. Fix is `uv sync --locked --no-dev` and `CMD ["uv", "run", "uvicorn", ...]`. Worth doing right after this plan; it is what would push us towards option C otherwise.
- **The app won't work end to end once deployed.** [apartment.ts](apartment-review-vue/src/stores/apartment.ts) calls `/api/apartments`, which the backend doesn't serve (its routes are `/user`, `/apartment`, `/`), and there is no CORS middleware. Both READMEs already list this; the smoke test above only covers `/`.
- **Neon connection string likely points at the wrong database.** `neonProject.connectionUri` is the project's *default* database (`neondb`), while the program also creates `apartment_review`; tables will be created in `neondb` on first start. Unverified until the first deploy; check which database has tables.
- **Postgres 18 locally, 16 on Neon** ([docker-compose.yml](apartment-review-vue/docker-compose.yml) vs [index.ts](infra/index.ts) `pgVersion: 16`).
- **`deploymentsEnabled` is a deprecated field** in the Cloudflare provider; `productionDeploymentEnabled` + `previewDeploymentSetting` replace it. Left untouched because it still works.
- **The two old repos** (`apartment-review-fastapi`, `apartment-review-vue`) are still live on GitHub. Archiving them avoids authorising the wrong one in Task 5.
- [DOCKER_GUIDE.md](apartment-review-vue/DOCKER_GUIDE.md) still lists the old ports (the README already notes this).
