# apartment-review — Claude Code instructions

Monorepo: `apartment-review-vue/` (Vue 3 frontend) and `apartment-review-fastapi/` (FastAPI backend). Each folder has its own `CLAUDE.md` with app-specific rules; read it before working in that folder.

## Always show the CLI commands

Whenever a lint, format, test, build or deploy step is run or described (locally or in CI), show the exact shell command and the folder it runs from, e.g. `cd apartment-review-fastapi && uv run flake8 .`. Never just say "lint passes".
