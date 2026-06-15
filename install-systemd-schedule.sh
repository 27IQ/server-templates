#!/usr/bin/env bash

set -euo pipefail

usage() {
  echo "Usage: $0 <template-directory>"
  echo
  echo "Creates and enables a systemd service and timer for scheduled Minecraft maintenance."
  echo "The timer uses RESTART_INTERVAL from <template-directory>/.env and Persistent=true."
}

if [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ]; then
  usage
  exit 0
fi

if [ "$#" -ne 1 ]; then
  usage
  exit 1
fi

template_dir="$(cd "$1" && pwd)"
env_file="$template_dir/.env"

if [ ! -f "$env_file" ]; then
  echo "Error: .env not found. Run ./install-template-hooks.sh $1 first."
  exit 1
fi

if [ ! -x "$template_dir/scheduled-maintenance.sh" ]; then
  echo "Error: scheduled-maintenance.sh not found. Run ./install-template-hooks.sh $1 first."
  exit 1
fi

set -a
. "$env_file"
set +a

: "${PACK_NAME:?PACK_NAME environment variable not set in .env!}"
RESTART_INTERVAL="${RESTART_INTERVAL:-24h}"

unit_name="$(printf '%s' "$PACK_NAME" | tr -c 'A-Za-z0-9_.@-' '-')"
service_name="${unit_name}-maintenance.service"
timer_name="${unit_name}-maintenance.timer"
systemd_dir="/etc/systemd/system"

sudo_cmd=""
if [ "$(id -u)" -ne 0 ]; then
  sudo_cmd="sudo"
fi

tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT

cat > "$tmp_dir/$service_name" <<EOF
[Unit]
Description=Minecraft maintenance for ${PACK_NAME}
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
WorkingDirectory=${template_dir}
ExecStart=${template_dir}/scheduled-maintenance.sh
EOF

cat > "$tmp_dir/$timer_name" <<EOF
[Unit]
Description=Run Minecraft maintenance for ${PACK_NAME} every ${RESTART_INTERVAL}

[Timer]
OnBootSec=5min
OnUnitActiveSec=${RESTART_INTERVAL}
Persistent=true
Unit=${service_name}

[Install]
WantedBy=timers.target
EOF

$sudo_cmd install -m 644 "$tmp_dir/$service_name" "$systemd_dir/$service_name"
$sudo_cmd install -m 644 "$tmp_dir/$timer_name" "$systemd_dir/$timer_name"
$sudo_cmd systemctl daemon-reload
$sudo_cmd systemctl enable --now "$timer_name"

echo "Installed and enabled $timer_name"
echo "Service: $service_name"
echo "Timer interval: $RESTART_INTERVAL"
