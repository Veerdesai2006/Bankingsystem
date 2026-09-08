#!/bin/bash
set -e

echo "[ENTRYPOINT] Starting SecureBank backend container..."

if [ -n "$DATABASE_URL" ]; then
    echo "[ENTRYPOINT] Verifying database connectivity..."
    python -c "
import sys, time
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError

db_url = '${DATABASE_URL}'
max_retries = 30
retry_interval = 2

for i in range(max_retries):
    try:
        engine = create_engine(db_url)
        with engine.connect() as conn:
            print('[ENTRYPOINT] Database connection established!')
            sys.exit(0)
    except Exception as e:
        print(f'[ENTRYPOINT] Waiting for database ({i+1}/{max_retries})...')
        time.sleep(retry_interval)

print('[ENTRYPOINT] ERROR: Could not connect to database after maximum retries.')
sys.exit(1)
"
fi

echo "[ENTRYPOINT] Running Alembic database migrations..."
alembic upgrade head
echo "[ENTRYPOINT] Database migrations complete."

echo "[ENTRYPOINT] Launching application process: $@"
exec "$@"
