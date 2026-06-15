#!/usr/bin/env bash

set -euo pipefail

RCON_HOST="${RCON_HOST:-127.0.0.1}"
RCON_PORT="${RCON_PORT:-25575}"
RCON_PWD="${RCON_PWD:?RCON_PWD environment variable not set!}"

if ! command -v mcrcon >/dev/null 2>&1; then
  echo "Error: mcrcon not found in PATH."
  exit 1
fi

if [ $# -eq 0 ]; then
  echo "Usage: $0 <rcon-command>"
  echo "Example: $0 'say Server will restart soon!'"
  exit 1
fi

mcrcon -H "$RCON_HOST" -P "$RCON_PORT" -p "$RCON_PWD" "$@"