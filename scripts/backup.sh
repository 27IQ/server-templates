#!/usr/bin/env bash

set -euo pipefail

if [ -f .env ]; then
  set -a
  . ./.env
  set +a
fi

: "${PACK_NAME:?PACK_NAME environment variable not set!}"

BACKUP_DIR="${BACKUP_DIR:-./backups}"
timestamp="$(date +%Y%m%d-%H%M%S)"
backup_file="${BACKUP_DIR}/${PACK_NAME}-${timestamp}.tar.gz"

mkdir -p "$BACKUP_DIR"

if [ -x ./mcron.sh ]; then
  ./mcron.sh "save-all flush" || true
  ./mcron.sh "save-off" || true
fi

cleanup() {
  if [ -x ./mcron.sh ]; then
    ./mcron.sh "save-on" || true
  fi
}
trap cleanup EXIT

docker exec "$PACK_NAME" sh -c '
  cd /opt/mcserver
  tar --exclude="*.jar" -czf - .
' > "$backup_file"

echo "Created backup: $backup_file"
