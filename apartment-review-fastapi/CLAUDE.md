# Apartment Review FastAPI - Claude Code Instructions

## Important Notes

- **Always** follow TDD: write tests first, then code
- **Always** use Railway-Oriented Programming with the `returns` library
- **Always** check for existing fixtures before creating new ones
- **Always** use Australian English in code and documentation
- **Never** use `pip` or `uv pip` anywhere, including the Dockerfile - use `uv add`/`uv remove`/`uv sync --locked`; get `uv` into an image with `COPY --from=ghcr.io/astral-sh/uv:<version> /uv /bin/uv`
- **Never** use mocking unless explicitly directed
