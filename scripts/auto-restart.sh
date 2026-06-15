#!/usr/bin/env bash

if [ -f .env ]; then
  set -a            # auto-export all variables
  . ./.env          # source it
  set +a
fi

docker exec "${PACK_NAME}" bash /opt/mcserver/auto-restart-container-hook.sh
docker compose restart

echo "Minecraft server restarted cleanly."
