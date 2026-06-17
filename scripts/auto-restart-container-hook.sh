#!/usr/bin/env bash

set -euo pipefail

if ! command -v rcon-cli >/dev/null 2>&1; then
  echo "Error: rcon-cli not found in PATH."
  exit 1
fi

say() {
  rcon-cli "say $*"
}

echo "Waiting for RCON to become ready..."
for i in {1..30}; do
  if rcon-cli "list" &>/dev/null; then
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

rcon-cli "save-all flush"
