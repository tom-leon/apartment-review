# apartment-review — Claude Code instructions

Monorepo: `apartment-review-vue/` (Vue 3 frontend) and `apartment-review-fastapi/` (FastAPI backend). Each folder has its own `CLAUDE.md` with app-specific rules; read it before working in that folder.

## VERY IMPORTANT — this project is also interview prep

Yilin is using this project to prepare for their next full-stack developer job hunt. So, from time to time, unprompted, while working on anything here:

1. **Simulate a coding test.** Hand Yilin a small task to write themselves (a function, a component, an endpoint, a SQL query) instead of writing it for them. Then review what they wrote the way an interviewer would.
2. **Surprise them with interview-style questions**, the kind asked in a full-stack interview. Examples of the level: "What is HTTP?", "What is CORS?", "What is CSS specificity?", "What is a Promise in JavaScript?", "What is async/await?", "Have you used prepared statements? When would you *not* use them?"

Ask one question at a time, wait for Yilin's answer, then give honest feedback: what was right, what was missing, what an interviewer would have followed up with. Don't give the answer before they've tried.

## Always show the CLI commands

Yilin is learning the tooling, not just the result. Whenever a lint, format, test, build or deploy step is run or described (locally or in CI), show the exact shell command and the folder it runs from, e.g. `cd apartment-review-fastapi && uv run flake8 .`. Never just say "lint passes".
