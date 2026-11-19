#!/usr/bin/env bash
# Wipe the local Docker database and fill it with the sample data in seed.sql
# (written by tools/dumpdb.sh). Run with the stack up: tools/reset-local-db.sh
set -e
cd "$(dirname "$0")/.."
docker compose exec -T db psql -U tom -d apartment_review -c 'DROP SCHEMA public CASCADE; CREATE SCHEMA public;'
# Tables are created from this machine, not the backend container: that image has
# newer library versions than uv.lock.
(cd ../apartment-review-fastapi && DATABASE_URL=postgresql://tom:123@localhost:5532/apartment_review uv run python -c 'from main import create_tables; create_tables()')
docker compose exec -T db psql -U tom -d apartment_review -q -v ON_ERROR_STOP=1 < ../apartment-review-fastapi/seed.sql
