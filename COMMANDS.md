# CLI commands used in this repo

Every command CI runs, plus the ones you run by hand. Learn these; they are the same in most companies.

## Backend (run from `apartment-review-fastapi/`)

| Command | What it does |
|---|---|
| `uv sync` | create `.venv` and install everything in `uv.lock` (dev tools included) |
| `uv sync --locked` | same, but fail if `pyproject.toml` and `uv.lock` disagree (what CI runs) |
| `uv add <pkg>` / `uv remove <pkg>` | add or drop a dependency and update the lockfile (never `uv pip`) |
| `uv lock --check` | just check the lockfile is in sync, install nothing |
| `uv run uvicorn main:app --reload` | start the API locally on port 8000, restart on file change |
| `uv run black .` | reformat every `.py` file (quotes, line breaks, indentation) |
| `uv run black --check .` | only report what black would change; exit 1 if anything (what CI runs) |
| `uv run flake8 .` | list unused imports, long lines, etc. per `.flake8`; exit 1 if any |
| `uv run pytest` | run all tests in `tests/` |
| `uv run pytest -q` | same, shorter output |
| `uv run pytest tests/test_main.py::test_name -v` | run one test |
| `docker build .` | build the Dockerfile the way DigitalOcean will |

`uv run <tool>` means "use this project's `.venv` copy of the tool". Nothing is installed globally.

## Frontend (run from `apartment-review-vue/`)

| Command | What it does |
|---|---|
| `nvm use` | switch to the Node version in `.nvmrc` (22) |
| `npm install` | install from `package.json`, updating `package-lock.json` if needed |
| `npm ci` | delete `node_modules`, install exactly `package-lock.json`; fail if out of sync (what CI runs) |
| `npm install -D <pkg>` | add a dev-only tool (goes in `devDependencies`) |
| `npm run dev` | start Vite's dev server on port 5173 with hot reload |
| `npm test` | run `vitest run`: every `*.spec.ts` once, then exit |
| `npx vitest` | same tests in watch mode, re-runs on save |
| `npm run type-check` | `vue-tsc --build`: TypeScript errors only, no output files |
| `npm run build-only` | `vite build`: bundle to `dist/` without type-checking |
| `npm run build` | type-check and build in parallel (what CI and Cloudflare run) |
| `npm run preview` | serve the built `dist/` locally to check the production bundle |

`npm run <name>` runs the script of that name in `package.json`. `npx <tool>` runs a tool from `node_modules/.bin`.

## Whole stack with Docker (run from `apartment-review-vue/`)

| Command | What it does |
|---|---|
| `docker compose up` | start Postgres (5532), the API (8100) and the frontend (5273) |
| `docker compose up -d` | same, in the background |
| `docker compose logs -f backend` | follow one service's logs |
| `docker compose down` | stop everything, keep the database volume |
| `docker compose down -v` | stop everything and delete the database |
| `docker compose exec db psql -U tom -d apartment_review` | open a SQL shell on the local database |

## Git (daily)

| Command | What it does |
|---|---|
| `git status --short` | what's changed, one line per file |
| `git diff` / `git diff -- <path>` | the actual changes, optionally for one path |
| `git diff -w` | same but ignore whitespace-only changes (handy after black) |
| `git add <path>` | stage one file or folder. Avoid `git add -A` in a dirty tree |
| `git commit -m "one line"` | commit what's staged |
| `git push` | send commits to GitHub (`origin main`) |
| `git fetch` | update your copy of what's on GitHub, touch nothing local |
| `git pull` | `fetch` + `merge` |
| `git pull --rebase` | `fetch` + replay your local commits on top, no merge commit |
| `git log --oneline -10` | last 10 commits, one line each |
| `git reflog` | every place HEAD has been; finds "lost" commits after a bad rebase |
| `git push --force-with-lease` | force-push, but refuse if someone pushed since your last fetch |
| `git remote -v` | which GitHub URL this clone pushes to |

## GitHub CLI (`gh`)

| Command | What it does |
|---|---|
| `gh auth status` | which account you're logged in as |
| `gh repo view --web` | open this repo on GitHub |
| `gh run list` | recent GitHub Actions runs |
| `gh run watch` | follow the current run in the terminal |
| `gh secret set NAME` | store a secret for Actions (prompts for the value) |
| `gh variable set NAME --body "value"` | store a non-secret variable for Actions |
| `gh pr merge <n> --squash --delete-branch` | merge a PR (Dependabot's) as one commit |

## Infrastructure (run from `apartment-review-vue/infra/`)

| Command | What it does |
|---|---|
| `pulumi stack ls` | list stacks (named deployments) for this program |
| `pulumi stack init dev` | create the `dev` stack |
| `pulumi config set key value` / `--secret` | set a config value; `--secret` encrypts it |
| `pulumi preview` | show what `up` would create/change, change nothing |
| `pulumi up` | create or update the cloud resources |
| `pulumi stack output backendUrl` | read one output; `--show-secrets` for secret ones |
| `pulumi destroy` | delete everything the stack created |
| `doctl apps create-deployment <app-id> --wait` | tell DigitalOcean to redeploy the API (what CI runs after tests) |
