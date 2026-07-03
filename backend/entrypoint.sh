#!/bin/bash
set -e

# Wait for MySQL to be ready using a Python socket check
echo "Waiting for MySQL to start..."
python -c "
import socket
import time
import os
import sys

host = os.getenv('MYSQL_HOST', 'mysql')
port = int(os.getenv('MYSQL_PORT', 3306))
print(f'Checking connection to {host}:{port}...')
for i in range(45):
    try:
        with socket.create_connection((host, port), timeout=2):
            print('MySQL is up!')
            sys.exit(0)
    except Exception:
        print(f'Waiting for MySQL to be ready... ({i}/45)')
        time.sleep(2)
sys.exit(1)
"

# Only run Alembic migrations if RUN_MIGRATIONS=true (backend service only)
if [ "${RUN_MIGRATIONS:-false}" = "true" ]; then
    echo "Running database migrations..."
    alembic upgrade head
    echo "Migrations complete."
fi

# Execute the CMD passed to docker run
exec "$@"
