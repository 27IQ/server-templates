#!/usr/bin/env bash

set -euo pipefail

if ! command -v rcon-cli >/dev/null 2>&1; then
  echo "Error: rcon-cli not found in PATH."
  exit 1
fi

if [ $# -eq 0 ]; then
  echo "Usage: $0 <rcon-command>"
  echo "Example: $0 'say Server will restart soon!'"
  exit 1
fi

rcon-cli "$@"
