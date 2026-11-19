#!/usr/bin/env bash
# Save the rows now in the local Docker database as the sample data that
# tools/reset-local-db.sh loads. Run with the stack up: tools/dumpdb.sh
set -e
cd "$(dirname "$0")/.."
docker compose exec -T db pg_dump -U tom -d apartment_review -a --column-inserts --restrict-key=seed > ../apartment-review-fastapi/seed.sql
