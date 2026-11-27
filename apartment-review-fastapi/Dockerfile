# Backend Dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY pyproject.toml .
COPY uv.lock .

# Install the pinned versions from uv.lock into the image's Python, same as the tests use
COPY --from=ghcr.io/astral-sh/uv:0.9.16 /uv /bin/uv
RUN UV_PROJECT_ENVIRONMENT=/usr/local uv sync --locked --no-dev --no-install-project

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Bring the database tables up to date, then run the application. A migration that
# fails stops the container from starting, so a broken deploy never serves.
CMD ["sh", "-c", "alembic upgrade head && exec uvicorn main:app --host 0.0.0.0 --port 8000"]
