#!/usr/bin/env bash

set -euo pipefail

usage() {
  echo "Usage: $0 [--remove-env] [--remove-server-dir] <template-directory>"
  echo
  echo "Removes helper scripts installed by install-template-hooks.sh."
  echo ".env is kept by default. Pass --remove-env to remove it too."
  echo "SERVER_DIR is kept by default. Pass --remove-server-dir to remove it too."
}

remove_env=false
remove_server_dir=false

if [ "${1:-}" = "-h" ] || [ "${1:-}" = "--help" ]; then
  usage
  exit 0
fi

while [ "$#" -gt 0 ]; do
  case "${1:-}" in
    --remove-env)
      remove_env=true
      shift
      ;;
    --remove-server-dir)
      remove_server_dir=true
      shift
      ;;
    *)
      break
      ;;
  esac
done

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

env_file="$template_dir/.env"
if [ ! -f "$env_file" ]; then
  env_file="$template_dir/.env-template"
fi

if [ "$remove_server_dir" = true ]; then
  if [ -f "$env_file" ]; then
    set -a
    . "$env_file"
    set +a

    SERVER_DIR="${SERVER_DIR:-./server}"
    case "$SERVER_DIR" in
      /*) server_dir="$SERVER_DIR" ;;
      *) server_dir="$template_dir/$SERVER_DIR" ;;
    esac

    if [ -d "$server_dir" ]; then
      rm -rf "$server_dir"
      echo "Removed $server_dir"
    else
      echo "Skipped missing $server_dir"
    fi
  else
    echo "Skipped SERVER_DIR removal because no .env or .env-template was found"
  fi
else
  echo "Kept SERVER_DIR"
fi

if [ -d "$template_dir/resources" ] && [ -z "$(find "$template_dir/resources" -mindepth 1 -print -quit)" ]; then
  rmdir "$template_dir/resources"
  echo "Removed empty $template_dir/resources"
fi

echo "Removed installed template helpers from $template_dir"
