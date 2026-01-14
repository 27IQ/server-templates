#!/usr/bin/env bash

docker exec -it minecraft-vanilla bash /opt/mcserver/auto-restart-container-hook.sh
docker compose restart

echo "Minecraft server restarted cleanly."