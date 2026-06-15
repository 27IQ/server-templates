#!/usr/bin/env bash

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$script_dir"

if [ -f .env ]; then
  set -a
  . ./.env
  set +a
fi

backup_enabled="${BACKUP_ENABLED:-false}"

case "${backup_enabled,,}" in
  true|1|yes|y|on)
    ./backup.sh
    ;;
  false|0|no|n|off)
    echo "Backup disabled by BACKUP_ENABLED=${BACKUP_ENABLED:-false}"
    ;;
  *)
    echo "Error: BACKUP_ENABLED must be true or false, got: $backup_enabled"
    exit 1
    ;;
esac

./auto-restart.sh
