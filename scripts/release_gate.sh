#!/usr/bin/env bash
set -uo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"
PYTHON_BIN="${SCMIRN_PYTHON:-python3}"

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
run_gate "Accountable personal-data approval" "${PYTHON_BIN}" scripts/check_data_governance.py --require-approved
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

if [[ -n "${SCMIRN_ENV_FILE:-}" && -f "${SCMIRN_ENV_FILE}" ]]; then
  run_gate "Production config validation and image build" scripts/deploy.sh build
else
  printf '\nBLOCKED: production config/build gate needs an explicit SCMIRN_ENV_FILE and CA files.\n' >&2
  failed=1
fi

blockers=(
  "Nine legacy tables and additional infrastructure/audit data remain quarantined without app/worker access; ownership-aware RLS and subject isolation are incomplete."
  "Staff MFA recovery, approved identity/federation, complete seven-role RBAC/ABAC review, reviewer separation, and deployment authorization remain open; staff APIs default off."
  "No scheduled retention purge, private object store/evidence lifecycle, production metrics/SLOs, SIEM alert owner, or synthetic production monitoring is configured."
  "Fresh SAST, SCA, container/OS and IaC scans, image SBOM, and signed build provenance are not complete for this candidate."
  "Backup/restore, disaster recovery, performance/capacity, rollback rehearsal, and multi-region resilience are not verified."
  "Accessibility requires route-wide automated and manual keyboard/screen-reader/reflow evidence."
  "The field registry is engineering-inventoried, but personal-data purpose/processing justification, processor, region, retention, rights workflow and accountable privacy approval are incomplete."
  "Government source onboarding, legal/privacy approvals, external security assessment and authorization remain external blockers."
)

printf '\n== Release blockers ==\n'
for blocker in "${blockers[@]}"; do
  printf 'BLOCKED: %s\n' "${blocker}"
done

if [[ "${failed}" -ne 0 ]]; then
  printf '\nRelease gate failed because one or more executable checks failed.\n' >&2
  exit 1
fi
printf '\nLocal automated checks passed, but release remains NOT PRODUCTION READY because the blockers above are unresolved.\n' >&2
exit 1
