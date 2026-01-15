#!/usr/bin/env bash

if [ -f .env ]; then
  set -a
  . ./.env
  set +a
fi

docker exec -it ${PACK_NAME} bash /opt/mcserver/mcron-container-hook.sh "$@"