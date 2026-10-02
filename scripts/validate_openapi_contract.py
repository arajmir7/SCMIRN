#!/usr/bin/env python3
"""Check the OpenAPI contract against the production allowlist and Flask routes."""

import re
import sys
from pathlib import Path

import yaml


repo_root = Path(__file__).resolve().parents[1]
backend_root = repo_root / "src/backend"
sys.path.insert(0, str(backend_root))

contract_path = repo_root / "docs/enterprise/openapi-enterprise.yaml"
with contract_path.open(encoding="utf-8") as contract_file:
    contract = yaml.safe_load(contract_file)

if not isinstance(contract, dict) or contract.get("openapi") != "3.1.0":
    raise SystemExit("OpenAPI contract must be a valid OpenAPI 3.1.0 document")
paths = contract.get("paths")
if not isinstance(paths, dict) or "/api/v1/triage" not in paths:
    raise SystemExit("OpenAPI contract is missing the source-gated triage route")

from app import create_app  # noqa: E402
from app.production_api import PRODUCTION_API_ALLOWLIST  # noqa: E402


HTTP_METHODS = {"get", "put", "post", "delete", "options", "head", "patch", "trace"}


def openapi_path(flask_rule: str) -> str:
    return re.sub(
        r"<(?:(?:[a-zA-Z_][a-zA-Z0-9_]*):)?([^>]+)>",
        r"{\1}",
        flask_rule,
    )


def sample_path(flask_rule: str) -> str:
    return re.sub(
        r"<(?:(?:[a-zA-Z_][a-zA-Z0-9_]*):)?([^>]+)>",
        lambda match: "test-file.txt" if match.group(1) == "filename" else "test-value",
        flask_rule,
    )


app = create_app("testing")
actual: dict[str, set[str]] = {}
api_rules = []
for rule in app.url_map.iter_rules():
    if not rule.rule.startswith("/api/"):
        continue
    normalized = openapi_path(rule.rule)
    methods = {method.lower() for method in rule.methods if method not in {"HEAD", "OPTIONS"}}
    actual.setdefault(normalized, set()).update(methods)
    api_rules.append((rule, methods))

documented: dict[str, set[str]] = {}
for path, operations in paths.items():
    if not isinstance(operations, dict):
        raise SystemExit(f"OpenAPI path item is invalid: {path}")
    documented[path] = {
        method.lower()
        for method in operations
        if method.lower() in HTTP_METHODS
    }

missing_paths = sorted(set(paths) - set(actual))
missing_methods = sorted(
    f"{path} {method.upper()}"
    for path, methods in documented.items()
    for method in methods
    if method not in actual.get(path, set())
)
undocumented_allowlist = sorted(
    f"{openapi_path(path)} {method}"
    for path, methods in PRODUCTION_API_ALLOWLIST.items()
    for method in methods
    if method.lower() not in documented.get(openapi_path(path), set())
)

if missing_paths or missing_methods or undocumented_allowlist:
    for item in missing_paths:
        print(f"Contract path is not registered: {item}", file=sys.stderr)
    for item in missing_methods:
        print(f"Contract method is not registered: {item}", file=sys.stderr)
    for item in undocumented_allowlist:
        print(f"Production-allowlisted operation is missing from contract: {item}", file=sys.stderr)
    raise SystemExit(1)

# Exercise every registered API method absent from the production allowlist.
# The readiness gate must reject it before its prototype handler can run.
app.config["SCMIRN_ENVIRONMENT"] = "production"
client = app.test_client()
blocked = 0
gate_failures = []
for rule, methods in api_rules:
    for method in methods:
        if method.upper() in PRODUCTION_API_ALLOWLIST.get(rule.rule, ()):
            continue
        response = client.open(sample_path(rule.rule), method=method.upper())
        blocked += 1
        if response.status_code != 503:
            gate_failures.append(f"{method.upper()} {rule.rule} returned {response.status_code}, expected 503")

if gate_failures:
    for failure in gate_failures:
        print(f"Production readiness gate failed: {failure}", file=sys.stderr)
    raise SystemExit(1)

print(
    f"OpenAPI 3.1 production route parity passed for {len(PRODUCTION_API_ALLOWLIST)} allowlisted paths; "
    f"the production gate rejected {blocked} other registered API operations."
)
