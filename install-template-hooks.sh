#!/usr/bin/env bash

set -euo pipefail

usage() {
  echo "Usage: $0 <template-directory>"
  echo
  echo "Installs the shared Minecraft helper scripts and .env into a docker template."
  echo "Host scripts are copied to the template root."
  echo "Container hooks are copied to <template-directory>/resources."
  echo ".env is created from <template-directory>/.env-template when missing."
  echo "SERVER_DIR and BACKUP_DIR are created from the template env."
}

if [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ]; then
  usage
  exit 0
fi

if [ "$#" -ne 1 ]; then
  usage
  exit 1
fi

repo_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
script_dir="$repo_dir/scripts"
template_dir="$1"

if [ ! -d "$template_dir" ]; then
  echo "Error: template directory does not exist: $template_dir"
  exit 1
fi

if [ ! -f "$template_dir/.env-template" ]; then
  echo "Error: .env-template not found in template directory: $template_dir"
  exit 1
fi

mkdir -p "$template_dir/resources"

install -m 755 "$script_dir/auto-restart.sh" "$template_dir/auto-restart.sh"
install -m 755 "$script_dir/mcron.sh" "$template_dir/mcron.sh"
install -m 755 "$script_dir/backup.sh" "$template_dir/backup.sh"
install -m 755 "$script_dir/scheduled-maintenance.sh" "$template_dir/scheduled-maintenance.sh"
install -m 755 "$script_dir/start-mcserver.sh" "$template_dir/resources/start-mcserver.sh"
install -m 755 "$script_dir/auto-restart-container-hook.sh" "$template_dir/resources/auto-restart-container-hook.sh"
install -m 755 "$script_dir/mcron-container-hook.sh" "$template_dir/resources/mcron-container-hook.sh"

if [ ! -f "$template_dir/.env" ]; then
  install -m 644 "$template_dir/.env-template" "$template_dir/.env"
  echo "Created $template_dir/.env from .env-template"
else
  echo "Skipped $template_dir/.env because it already exists"
fi

set -a
. "$template_dir/.env"
set +a

SERVER_DIR="${SERVER_DIR:-./server}"
BACKUP_DIR="${BACKUP_DIR:-./backups}"

create_data_dir() {
  local configured_path="$1"
  local description="$2"
  local data_dir

  case "$configured_path" in
    /*) data_dir="$configured_path" ;;
    *) data_dir="$template_dir/$configured_path" ;;
  esac

  mkdir -p "$data_dir"
  chmod 1000 "$data_dir"
  echo "Created $description directory: $data_dir"
}

create_data_dir "$SERVER_DIR" "server data"
create_data_dir "$BACKUP_DIR" "backup"

echo "Installed shared hooks into $template_dir"
