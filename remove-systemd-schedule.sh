#!/usr/bin/env bash

set -euo pipefail

usage() {
  echo "Usage: $0 <template-directory>"
  echo
  echo "Disables and removes the systemd service and timer created by install-systemd-schedule.sh."
  echo "PACK_NAME is read from <template-directory>/.env, falling back to .env-template."
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
  env_file="$template_dir/.env-template"
fi

if [ ! -f "$env_file" ]; then
  echo "Error: neither .env nor .env-template found in template directory: $template_dir"
  exit 1
fi

set -a
. "$env_file"
set +a

: "${PACK_NAME:?PACK_NAME environment variable not set in $env_file!}"

unit_name="$(printf '%s' "$PACK_NAME" | tr -c 'A-Za-z0-9_.@-' '-')"
service_name="${unit_name}-maintenance.service"
timer_name="${unit_name}-maintenance.timer"
systemd_dir="/etc/systemd/system"

sudo_cmd=""
if [ "$(id -u)" -ne 0 ]; then
  sudo_cmd="sudo"
fi

$sudo_cmd systemctl disable --now "$timer_name" || true
$sudo_cmd systemctl stop "$service_name" || true
$sudo_cmd rm -f "$systemd_dir/$timer_name" "$systemd_dir/$service_name"
$sudo_cmd systemctl daemon-reload
$sudo_cmd systemctl reset-failed "$timer_name" "$service_name" || true

echo "Removed $timer_name"
echo "Removed $service_name"
