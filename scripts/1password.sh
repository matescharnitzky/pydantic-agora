#!/usr/bin/env bash
set -euo pipefail

cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.."

if [[ $# -eq 0 ]]; then
  echo 'Usage: scripts/1password.sh command [arguments...]' >&2
  exit 2
fi
environment_id=""
if [[ "${COMPOSE_DISABLE_ENV_FILE:-}" != "1" && -f .env ]]; then
  environment_id=$(sed -n 's/^OP_ENVIRONMENT_ID=//p' .env)
fi
if [[ -z "$environment_id" ]]; then
  exec "$@"
fi
if [[ ! "$environment_id" =~ ^[a-zA-Z0-9_-]+$ ]]; then
  echo 'Set one unquoted OP_ENVIRONMENT_ID=your-id line in .env.' >&2
  exit 2
fi

exec op run --env-file .env --environment "$environment_id" -- "$@"
