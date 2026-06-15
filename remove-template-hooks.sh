#!/usr/bin/env bash

set -euo pipefail

usage() {
  echo "Usage: $0 [--remove-env] <template-directory>"
  echo
  echo "Removes helper scripts installed by install-template-hooks.sh."
  echo ".env is kept by default. Pass --remove-env to remove it too."
}

remove_env=false

if [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ]; then
  usage
  exit 0
fi

if [ "${1:-}" = "--remove-env" ]; then
  remove_env=true
  shift
fi

if [ "$#" -ne 1 ]; then
  usage
  exit 1
fi

template_dir="$1"

if [ ! -d "$template_dir" ]; then
  echo "Error: template directory does not exist: $template_dir"
  exit 1
fi

remove_file() {
  local path="$1"

  if [ -e "$path" ]; then
    rm -f "$path"
    echo "Removed $path"
  else
    echo "Skipped missing $path"
  fi
}

remove_file "$template_dir/auto-restart.sh"
remove_file "$template_dir/mcron.sh"
remove_file "$template_dir/backup.sh"
remove_file "$template_dir/scheduled-maintenance.sh"
remove_file "$template_dir/resources/auto-restart-container-hook.sh"
remove_file "$template_dir/resources/mcron-container-hook.sh"

if [ "$remove_env" = true ]; then
  remove_file "$template_dir/.env"
else
  echo "Kept $template_dir/.env"
fi

if [ -d "$template_dir/resources" ] && [ -z "$(find "$template_dir/resources" -mindepth 1 -print -quit)" ]; then
  rmdir "$template_dir/resources"
  echo "Removed empty $template_dir/resources"
fi

echo "Removed installed template helpers from $template_dir"
