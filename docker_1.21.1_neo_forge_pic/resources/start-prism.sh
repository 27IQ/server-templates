#!/usr/bin/env bash
set -euo pipefail

python3 /usr/local/bin/prism-mods.py
exec java @user_jvm_args.txt @libraries/net/neoforged/neoforge/21.1.259/unix_args.txt nogui "$@"
