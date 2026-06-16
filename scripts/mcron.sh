#!/usr/bin/env bash

set -euo pipefail

if [ -f .env ]; then
  set -a
  . ./.env
  set +a
fi

docker exec "${PACK_NAME}" /extras/mcron-container-hook.sh "$@"
