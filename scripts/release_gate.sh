#!/usr/bin/env bash
set -uo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"
PYTHON_BIN="${SCMIRN_PYTHON:-python3}"
MODE="${SCMIRN_RELEASE_MODE:-candidate}"
if [[ "$#" -eq 1 ]]; then
  MODE="$1"
elif [[ "$#" -eq 2 && "$1" == "--mode" ]]; then
  MODE="$2"
elif [[ "$#" -gt 0 ]]; then
  printf 'Usage: %s [candidate|authorized] or %s --mode [candidate|authorized]\n' "$0" "$0" >&2
  exit 2
fi
if [[ "${MODE}" != "candidate" && "${MODE}" != "authorized" ]]; then
  printf 'Usage: %s [candidate|authorized] or %s --mode [candidate|authorized]\n' "$0" "$0" >&2
  exit 2
fi

failed=0
run_gate() {
  local label="$1"
  shift
  printf '\n== %s ==\n' "${label}"
  if "$@"; then
    printf 'PASS: %s\n' "${label}"
  else
    local status=$?
    printf 'FAIL (%s): %s\n' "${status}" "${label}" >&2
    failed=1
  fi
}

run_gate "Backend unit, integration and policy tests" "${PYTHON_BIN}" -m pytest -q -p no:cacheprovider src/backend/tests
run_gate "Persisted data governance inventory parity" "${PYTHON_BIN}" scripts/check_data_governance.py
if [[ -n "${SCMIRN_POSTGRES_RLS_TEST_URL:-}" ]]; then
  printf 'PostgreSQL RLS integration is enabled with the supplied disposable-test URL.\n'
else
  printf 'BLOCKED: set SCMIRN_POSTGRES_RLS_TEST_URL to a disposable PostgreSQL instance; database boundary tests are opt-in.\n' >&2
  failed=1
fi
run_gate "Frontend typecheck" npm --prefix src/frontend run typecheck
run_gate "Frontend production build" npm --prefix src/frontend run build
run_gate "Frontend browser flows" npm --prefix src/frontend run test:e2e
run_gate "Feature parity ledger" "${PYTHON_BIN}" scripts/check_feature_parity.py
run_gate "OpenAPI syntax and route/method parity" "${PYTHON_BIN}" scripts/validate_openapi_contract.py
run_gate "Typed blocker ledger and categorized governance report" "${PYTHON_BIN}" scripts/check_release_blockers.py --mode "${MODE}"

if [[ -n "${SCMIRN_ENV_FILE:-}" && -f "${SCMIRN_ENV_FILE}" ]]; then
  run_gate "Production config validation and image build" scripts/deploy.sh build
else
  printf '\nBLOCKED_EXTERNAL_DEPENDENCY: production config/build gate needs an authorized SCMIRN_ENV_FILE, deployment secrets and CA files.\n' >&2
  if [[ "${MODE}" == "authorized" ]]; then
    failed=1
  fi
fi

if [[ "${failed}" -ne 0 ]]; then
  if [[ "${MODE}" == "authorized" ]]; then
    printf '\nAUTHORIZED DEPLOYMENT GATE FAILED: local checks or external evidence are incomplete.\n' >&2
  else
    printf '\nENGINEERING CANDIDATE GATE FAILED: local checks or blocking engineering evidence are incomplete.\n' >&2
  fi
  exit 1
fi
if [[ "${MODE}" == "authorized" ]]; then
  printf '\nAUTHORIZED GOVERNMENT PRODUCTION DEPLOYMENT: gates passed.\n'
else
  printf '\nENGINEERING RELEASE CANDIDATE: local gates passed; external approvals remain recorded in the blocker ledger.\n'
fi
