#!/bin/sh
set -e

# Run database migrations automatically if DATABASE_URL is set
if [ -n "$DATABASE_URL" ]; then
    echo "[Entrypoint] Running database migrations (alembic upgrade head)..."
    alembic upgrade head || {
        echo "[Entrypoint] Migration failed or skipped. Continuing startup..."
    }
fi

# Execute the container command
exec "$@"
