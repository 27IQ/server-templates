#!/usr/bin/env bash

set -euo pipefail

RCON_HOST="${RCON_HOST:-127.0.0.1}"
RCON_PORT="${RCON_PORT:-25575}"
RCON_PWD="${RCON_PWD:?RCON_PWD environment variable not set!}"
MCRCON_BIN="${MCRCON_BIN:-/usr/local/bin/mcrcon}"

if [ ! -x "$MCRCON_BIN" ]; then
  echo "Error: mcrcon binary not found at $MCRCON_BIN."
  exit 1
fi

say() {
  "$MCRCON_BIN" -H "$RCON_HOST" -P "$RCON_PORT" -p "$RCON_PWD" "say $*"
}

echo "Waiting for RCON at ${RCON_HOST}:${RCON_PORT}..."
for i in {1..30}; do
  if "$MCRCON_BIN" -H "$RCON_HOST" -P "$RCON_PORT" -p "$RCON_PWD" "list" &>/dev/null; then
    echo "RCON is ready."
    break
  fi
  echo "  ... still waiting ($i)"
  sleep 2
done

say "Server restarting in 60 seconds! Please find a safe spot."
sleep 30
say "Server restarting in 30 seconds!"
sleep 20
say "Server restarting in 10 seconds!"
sleep 5
for n in 5 4 3 2 1; do
  say "$n..."
  sleep 1
done
say "Restarting now!"

"$MCRCON_BIN" -H "$RCON_HOST" -P "$RCON_PORT" -p "$RCON_PWD" "save-all flush"