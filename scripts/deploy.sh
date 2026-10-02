#!/usr/bin/env bash
set -Eeuo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="${SCMIRN_PRODUCTION_COMPOSE_FILE:-${ROOT_DIR}/infrastructure/docker-compose.production.yml}"
ENV_FILE="${SCMIRN_ENV_FILE:-${ROOT_DIR}/.env.production}"
PROJECT_NAME="${SCMIRN_COMPOSE_PROJECT_NAME:-scmirn-production}"
ACTION="${1:-help}"

usage() {
  cat <<'EOF'
Usage: scripts/deploy.sh <validate|build|deploy|rollback|status|logs|stop>

Uses infrastructure/docker-compose.production.yml and .env.production.
The web container binds to localhost; place it behind an HTTPS reverse proxy.
build/deploy require an unused local SCMIRN_RELEASE_ID; rollback selects retained local images and never builds or pulls them.
This script does not provision external services or claim production approval.
EOF
}

if [[ "${ACTION}" == "help" || "${ACTION}" == "-h" || "${ACTION}" == "--help" ]]; then
  usage
  exit 0
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "ERROR: docker is required." >&2
  exit 1
fi
if [[ ! -f "${COMPOSE_FILE}" ]]; then
  echo "ERROR: production Compose file not found: ${COMPOSE_FILE}" >&2
  exit 1
fi
if [[ ! -f "${ENV_FILE}" ]]; then
  echo "ERROR: production environment file not found: ${ENV_FILE}" >&2
  echo "Copy .env.production.example to .env.production and replace every placeholder." >&2
  exit 1
fi

compose() {
  docker compose --project-name "${PROJECT_NAME}" --env-file "${ENV_FILE}" -f "${COMPOSE_FILE}" "$@"
}

check_environment() {
  python3 "${ROOT_DIR}/scripts/validate_production_config.py" --env-file "${ENV_FILE}"
}

validate() {
  check_environment
  compose config --quiet
  echo "Compose configuration is valid. External PostgreSQL and TLS Redis are not contacted by this check."
}

release_id() {
  python3 - "${ENV_FILE}" "${ROOT_DIR}" <<'PY'
import sys
from pathlib import Path
sys.path.insert(0, str(Path(sys.argv[2]) / 'scripts'))
from validate_production_config import parse_env_file
print(parse_env_file(Path(sys.argv[1]))['SCMIRN_RELEASE_ID'])
PY
}

ensure_release_tags_unused() {
  local identifier
  identifier="$(release_id)"
  for image in scmirn/backend scmirn/frontend; do
    if docker image inspect "${image}:${identifier}" >/dev/null 2>&1; then
      echo "ERROR: immutable release tag ${image}:${identifier} already exists locally; choose a new SCMIRN_RELEASE_ID." >&2
      return 1
    fi
  done
}

smoke_deployment() {
  local http_port
  http_port="$(awk -F= '$1 == "SCMIRN_HTTP_PORT" { print $2 }' "${ENV_FILE}")"
  http_port="${http_port:-8080}"
  local site_url="http://127.0.0.1:${http_port}"
  curl --fail --silent --show-error "${site_url}/" >/dev/null
  curl --fail --silent --show-error "${site_url}/documents" >/dev/null
  local health_body
  health_body="$(curl --fail --silent --show-error "${site_url}/api/ready")"
  if [[ "${health_body}" != *'"status":"ready"'* && "${health_body}" != *'"status": "ready"'* ]]; then
    echo "ERROR: proxied API health check returned an unexpected response." >&2
    return 1
  fi
  local legacy_status
  legacy_status="$(curl --output /dev/null --write-out '%{http_code}' --silent --show-error "${site_url}/api/offices")"
  if [[ "${legacy_status}" != "503" ]]; then
    echo "ERROR: production API boundary expected /api/offices to return 503; received ${legacy_status}." >&2
    return 1
  fi
}

case "${ACTION}" in
  validate)
    validate
    ;;
  build)
    validate
    ensure_release_tags_unused
    compose build
    ;;
  deploy)
    if ! command -v curl >/dev/null 2>&1; then
      echo "ERROR: curl is required for the local deployment smoke check." >&2
      exit 1
    fi
    validate
    ensure_release_tags_unused
    compose build
    compose up --detach --wait --wait-timeout 180
    compose ps
    smoke_deployment
    echo "Release ID: $(release_id)"
    docker image inspect --format '{{.RepoTags}} {{.Id}}' "scmirn/backend:$(release_id)" "scmirn/frontend:$(release_id)"
    echo "Local deployment smoke passed: frontend root, nested route, proxied API readiness, and disabled legacy API boundary."
    echo "Confirm the upstream TLS proxy, backups, monitoring, security review, and approved integrations separately."
    ;;
  rollback)
    if ! command -v curl >/dev/null 2>&1; then
      echo "ERROR: curl is required for the rollback smoke check." >&2
      exit 1
    fi
    validate
    rollback_id="$(release_id)"
    docker image inspect "scmirn/backend:${rollback_id}" "scmirn/frontend:${rollback_id}" >/dev/null || {
      echo "ERROR: rollback images for release ${rollback_id} are not present locally; refusing to build or pull them." >&2
      exit 1
    }
    # Do not re-run the migration service while switching application images.
    # The already-running database and Redis stay untouched.
    compose up --pull never --no-deps --detach --wait --wait-timeout 180 backend frontend
    compose ps
    smoke_deployment
    echo "Rollback smoke passed for retained release ID ${rollback_id}. Migration compatibility still requires operator approval."
    ;;
  status)
    compose ps
    ;;
  logs)
    compose logs --follow --tail=200
    ;;
  stop)
    compose stop
    ;;
  *)
    usage >&2
    exit 2
    ;;
esac
