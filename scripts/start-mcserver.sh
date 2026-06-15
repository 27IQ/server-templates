#!/usr/bin/env bash

set -euo pipefail

template_dir="/opt/mcserver-template"
server_dir="/opt/mcserver"

mkdir -p "$server_dir"

if [ ! -f "$server_dir/start.sh" ]; then
  echo "Seeding $server_dir from $template_dir..."
  cp -a "$template_dir/." "$server_dir/"
fi

for hook in auto-restart-container-hook.sh mcron-container-hook.sh; do
  if [ -f "$template_dir/$hook" ]; then
    cp "$template_dir/$hook" "$server_dir/$hook"
    chmod +x "$server_dir/$hook"
  fi
done

cd "$server_dir"
chmod +x start.sh
exec ./start.sh
