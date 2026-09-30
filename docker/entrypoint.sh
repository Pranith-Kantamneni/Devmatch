#!/bin/sh
set -e

echo "Waiting for database to be available..."
python3 - <<'PY'
import os
import socket
import time
from urllib.parse import urlparse

url = os.environ.get("DATABASE_URL", "")
host = urlparse(url).hostname or "db"
port = urlparse(url).port or 5432

for _ in range(60):
    try:
        with socket.create_connection((host, port), timeout=2):
            print(f"Database at {host}:{port} is reachable.")
            break
    except OSError:
        time.sleep(1)
else:
    print(f"Database at {host}:{port} is not reachable after 60s.")
    raise SystemExit(1)
PY

exec "$@"
