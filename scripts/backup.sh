#!/usr/bin/env bash

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$script_dir"

if [ -f .env ]; then
  set -a
  . ./.env
  set +a
fi

: "${PACK_NAME:?PACK_NAME environment variable not set!}"

BACKUP_DIR="${BACKUP_DIR:-./backups}"
BACKUP_WARNING_SECONDS="${BACKUP_WARNING_SECONDS:-60}"
timestamp="$(date +%Y%m%d-%H%M%S)"
backup_file="${BACKUP_DIR}/${PACK_NAME}-${timestamp}.tar.gz"

mkdir -p "$BACKUP_DIR"

if [ ! -x ./mcron.sh ]; then
  echo "Error: ./mcron.sh is required so backup can warn players and pause saves safely."
  exit 1
fi

if ! [[ "$BACKUP_WARNING_SECONDS" =~ ^[0-9]+$ ]]; then
  echo "Error: BACKUP_WARNING_SECONDS must be a non-negative integer, got: $BACKUP_WARNING_SECONDS"
  exit 1
fi

mcron() {
  ./mcron.sh "$@"
}

say() {
  mcron "say $*"
}

announce_countdown() {
  local remaining="$1"
  local mark

  if [ "$remaining" -le 0 ]; then
    return
  fi

  say "Server backup starting in ${remaining} seconds! You may notice a short save pause."

  for mark in 60 30 10 5 4 3 2 1; do
    if [ "$remaining" -gt "$mark" ]; then
      sleep "$((remaining - mark))"
      remaining="$mark"

      if [ "$mark" -gt 5 ]; then
        say "Server backup starting in ${mark} seconds!"
      else
        say "$mark..."
      fi
    fi
  done

  sleep "$remaining"
  say "Starting backup now."
}

cleanup() {
  mcron "save-on" || true
}
trap cleanup EXIT

announce_countdown "$BACKUP_WARNING_SECONDS"
mcron "save-all flush"
mcron "save-off"

docker exec "$PACK_NAME" sh -c '
  cd /data
  tar --exclude="*.jar" -czf - .
' > "$backup_file"

mcron "save-on"
trap - EXIT

echo "Created backup: $backup_file"
