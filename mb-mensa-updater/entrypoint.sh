#!/bin/sh
set -e

echo "[entrypoint] Crontab:"
cat /etc/crontabs/root

echo "[entrypoint] Running update.sh once on startup..."
/app/update.sh

echo "[entrypoint] Starting crond..."
exec crond -f -l 2
