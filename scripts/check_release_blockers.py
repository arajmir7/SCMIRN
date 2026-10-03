#!/usr/bin/env python3
"""Validate the production blocker ledger and report candidate/deployment gates."""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import date, datetime, timezone
import hashlib
import re
import shutil
import subprocess
import sys
import os
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "docs/release/production-blockers.yaml"
TYPES = {
    "ENGINEERING", "OPERATIONAL", "PRIVACY_LEGAL", "EXTERNAL_SECURITY_REVIEW",
    "GOVERNMENT_AUTHORIZATION", "INFRASTRUCTURE",
}
STATES = {
    "OPEN", "IMPLEMENTED", "LOCALLY_VERIFIED", "EXTERNALLY_VERIFIED",
    "WAIVED_WITH_AUTHORITY", "BLOCKED_EXTERNAL_DEPENDENCY",
}
SEVERITIES = {"CRITICAL", "HIGH", "MEDIUM", "LOW"}
REQUIRED_FIELDS = {
    "id", "title", "category", "severity", "type", "state",
    "production_blocking", "owner_role", "source_requirement",
    "affected_component", "verification_command", "required_evidence",
    "last_verified_commit", "last_verified_date", "closure_reason",
}
COMPLETED_STATES = {"LOCALLY_VERIFIED", "EXTERNALLY_VERIFIED", "WAIVED_WITH_AUTHORITY"}
EXTERNAL_TYPES = {
    "OPERATIONAL", "PRIVACY_LEGAL", "EXTERNAL_SECURITY_REVIEW",
    "GOVERNMENT_AUTHORIZATION", "INFRASTRUCTURE",
}
REQUIRED_BASELINE_IDS = {
    *(f"ENG-{number:03d}" for number in range(1, 13)),
    *(f"PRIV-{number:03d}" for number in range(1, 4)),
    *(f"EXT-{number:03d}" for number in range(1, 6)),
}


def load_ledger(path: Path = LEDGER) -> dict[str, Any]:
    value = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or not isinstance(value.get("blockers"), list):
        raise ValueError("Blocker ledger must contain a blockers list.")
    return value


def _head(root: Path) -> str:
    return subprocess.run(
        ["git", "-C", str(root), "rev-parse", "HEAD"],
        check=True, capture_output=True, text=True,
    ).stdout.strip()


def _evidence_path(root: Path, value: str) -> Path | None:
    candidate = Path(value)
    if candidate.is_absolute() or ".." in candidate.parts:
        return None
    path = (root / candidate).resolve()
    try:
        path.relative_to(root.resolve())
    except ValueError:
        return None
    return path


def _verify_authority_signature(evidence: Path, *, root: Path) -> str | None:
    """Require an external detached signature rooted outside the source tree."""
    keyring_value = os.environ.get("SCMIRN_RELEASE_TRUSTED_KEYRING", "")
    fingerprints = {
        value.replace(" ", "").upper()
        for value in os.environ.get("SCMIRN_RELEASE_TRUSTED_FINGERPRINTS", "").split(",")
        if value.strip()
    }
    if not keyring_value or not fingerprints:
        return "external completion requires a protected trusted-keyring path and allowlisted signer fingerprints"
    keyring = Path(keyring_value)
    if not keyring.is_absolute():
        return "trusted authority keyring path must be absolute and supplied by the deployment environment"
    try:
        keyring.resolve().relative_to(root.resolve())
    except ValueError:
        pass
    else:
        return "trusted authority keyring must be mounted outside the repository"
    if not keyring.is_file():
        return "trusted authority keyring is unavailable"
    if any(not re.fullmatch(r"(?:[0-9A-F]{40}|[0-9A-F]{64})", value) for value in fingerprints):
        return "trusted signer fingerprint allowlist contains an invalid fingerprint"
    verifier = shutil.which("gpgv")
    if not verifier:
        return "gpgv is unavailable; external evidence cannot be verified"
    signature = Path(f"{evidence}.sig")
    if not signature.is_file():
        return "detached authority signature is missing"
    result = subprocess.run(
        [verifier, "--status-fd", "1", "--keyring", str(keyring), str(signature), str(evidence)],
        check=False, capture_output=True, text=True,
    )
    if result.returncode != 0:
        return "detached authority signature did not verify"
    signed_by = {
        match.group(1).upper()
        for match in re.finditer(r"\[GNUPG:\] VALIDSIG ([0-9A-F]+)", result.stdout)
    }
    if not signed_by.intersection(fingerprints):
        return "detached evidence signer is not in the protected fingerprint allowlist"
    return None


def _verify_evidence_manifest(
    evidence: Path, *, blocker: dict[str, Any], root: Path,
    commit: str, verified_date: str,
) -> list[str]:
    errors: list[str] = []
    try:
        manifest = yaml.safe_load(evidence.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, yaml.YAMLError):
        return ["required evidence must be a readable YAML/JSON attestation manifest"]
    if not isinstance(manifest, dict):
        return ["required evidence must contain an attestation mapping"]
    expected = {
        "blocker_id": blocker["id"],
        "state": blocker["state"],
        "verified_commit": commit,
        "verified_at": verified_date,
    }
    for name, value in expected.items():
        if manifest.get(name) != value:
            errors.append(f"evidence manifest {name} does not match the ledger")
    if blocker["state"] in {"EXTERNALLY_VERIFIED", "WAIVED_WITH_AUTHORITY"}:
        for name in ("approver_identity", "approver_organization", "approval_reference", "artifact_path", "artifact_sha256"):
            if not isinstance(manifest.get(name), str) or not manifest[name].strip():
                errors.append(f"external evidence manifest is missing {name}")
        artifact_path_value = manifest.get("artifact_path")
        artifact_digest = manifest.get("artifact_sha256")
        if isinstance(artifact_path_value, str) and isinstance(artifact_digest, str):
            artifact = _evidence_path(root, artifact_path_value)
            if artifact is None or not artifact.is_file():
                errors.append("external approval artifact is missing or outside the repository evidence directory")
            elif not re.fullmatch(r"[0-9a-f]{64}", artifact_digest):
                errors.append("external evidence artifact digest is not a lowercase SHA-256 value")
            elif _sha256_file(artifact) != artifact_digest:
                errors.append("external evidence artifact SHA-256 does not match the signed manifest")
        if blocker["state"] == "WAIVED_WITH_AUTHORITY" and not manifest.get("waiver_reason"):
            errors.append("authority waiver manifest is missing waiver_reason")
    return errors


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def validate_inventory(ledger: dict[str, Any]) -> list[str]:
    """Prevent the release ledger from passing after baseline controls are deleted."""
    present = {
        blocker.get("id") for blocker in ledger.get("blockers", [])
        if isinstance(blocker, dict)
    }
    missing = sorted(REQUIRED_BASELINE_IDS - present)
    if missing:
        return ["Required baseline blocker records are missing: " + ", ".join(missing) + "."]
    return []


def validate_ledger(ledger: dict[str, Any], *, root: Path = ROOT, mode: str = "candidate", today: date | None = None) -> list[str]:
    errors: list[str] = []
    if ledger.get("schema_version") != 1:
        errors.append("Unsupported production blocker ledger schema_version.")
    if mode not in {"candidate", "authorized"}:
        errors.append("mode must be candidate or authorized.")
    try:
        head = _head(root)
    except (OSError, subprocess.CalledProcessError):
        head = ""
        errors.append("Could not resolve the repository HEAD for evidence binding.")
    today = today or datetime.now(timezone.utc).date()
    ids: set[str] = set()

    for index, blocker in enumerate(ledger["blockers"]):
        label = blocker.get("id", f"<blocker-{index}>") if isinstance(blocker, dict) else f"<blocker-{index}>"
        if not isinstance(blocker, dict):
            errors.append(f"{label}: blocker must be a mapping.")
            continue
        missing = sorted(REQUIRED_FIELDS - set(blocker))
        if missing:
            errors.append(f"{label}: missing required fields {missing}.")
            continue
        if not re.fullmatch(r"[A-Z][A-Z0-9]*-[0-9]{3}", str(blocker["id"])):
            errors.append(f"{label}: id must be stable uppercase text followed by a three-digit number.")
        if label in ids:
            errors.append(f"{label}: duplicate blocker id.")
        ids.add(label)
        if blocker["type"] not in TYPES:
            errors.append(f"{label}: unsupported type {blocker['type']!r}.")
        if blocker["state"] not in STATES:
            errors.append(f"{label}: unsupported state {blocker['state']!r}.")
        if blocker["severity"] not in SEVERITIES:
            errors.append(f"{label}: unsupported severity {blocker['severity']!r}.")
        for key in ("title", "category", "owner_role", "source_requirement", "affected_component", "verification_command", "required_evidence"):
            if not isinstance(blocker[key], str) or not blocker[key].strip():
                errors.append(f"{label}: {key} must be a non-empty string.")
        if not isinstance(blocker["production_blocking"], bool):
            errors.append(f"{label}: production_blocking must be a boolean.")

        external = blocker["type"] in EXTERNAL_TYPES
        if external and blocker["state"] in {"OPEN", "IMPLEMENTED", "LOCALLY_VERIFIED"}:
            errors.append(f"{label}: external requirement must be blocked pending dependency or carry signed external evidence.")
        if not external and blocker["state"] == "BLOCKED_EXTERNAL_DEPENDENCY":
            errors.append(f"{label}: engineering/operational work cannot be hidden as an external dependency.")
        if blocker["state"] == "EXTERNALLY_VERIFIED" and not external:
            errors.append(f"{label}: EXTERNALLY_VERIFIED is reserved for an external requirement.")
        if blocker["state"] == "WAIVED_WITH_AUTHORITY" and not external:
            errors.append(f"{label}: only an external requirement may be waived with authority evidence.")

        if blocker["state"] in COMPLETED_STATES:
            commit = blocker["last_verified_commit"]
            verified_date = blocker["last_verified_date"]
            if not isinstance(blocker["closure_reason"], str) or not blocker["closure_reason"].strip():
                errors.append(f"{label}: completed state needs a non-empty closure_reason.")
            if not isinstance(commit, str) or not re.fullmatch(r"[0-9a-f]{40}", commit):
                errors.append(f"{label}: completed state needs a full last_verified_commit.")
            elif commit != head:
                errors.append(f"{label}: evidence commit {commit} is stale; current commit is {head}.")
            if not isinstance(verified_date, str):
                errors.append(f"{label}: completed state needs last_verified_date.")
                verified = None
            else:
                try:
                    verified = date.fromisoformat(verified_date)
                except ValueError:
                    verified = None
                    errors.append(f"{label}: last_verified_date must be ISO YYYY-MM-DD.")
            if verified is not None and verified > today:
                errors.append(f"{label}: evidence verification date is in the future.")
            evidence = _evidence_path(root, blocker["required_evidence"])
            if evidence is None:
                errors.append(f"{label}: required_evidence must be a safe repository-relative path.")
            elif not evidence.is_file():
                errors.append(f"{label}: required evidence file is missing: {blocker['required_evidence']}.")
            elif isinstance(commit, str) and isinstance(verified_date, str):
                for manifest_error in _verify_evidence_manifest(
                    evidence, blocker=blocker, root=root,
                    commit=commit, verified_date=verified_date,
                ):
                    errors.append(f"{label}: {manifest_error}.")
            if blocker["state"] == "WAIVED_WITH_AUTHORITY" and not blocker.get("closure_reason"):
                errors.append(f"{label}: an authority waiver needs a recorded closure_reason.")
            if blocker["state"] in {"EXTERNALLY_VERIFIED", "WAIVED_WITH_AUTHORITY"} and evidence is not None and evidence.is_file():
                signature_error = _verify_authority_signature(evidence, root=root)
                if signature_error:
                    errors.append(f"{label}: {signature_error}.")
            max_age = blocker.get("evidence_max_age_days")
            if max_age is not None and (not isinstance(max_age, int) or isinstance(max_age, bool) or max_age < 1):
                errors.append(f"{label}: evidence_max_age_days must be a positive integer.")
                max_age = None
            if max_age is not None and verified is not None and (today - verified).days > max_age:
                errors.append(f"{label}: evidence is stale ({(today - verified).days} days; maximum {max_age}).")
        elif blocker["last_verified_commit"] is not None or blocker["last_verified_date"] is not None:
            errors.append(f"{label}: open or externally blocked item cannot carry a completed verification stamp.")

        if mode == "candidate" and blocker["production_blocking"] and blocker["state"] in {"OPEN", "IMPLEMENTED"}:
            errors.append(f"{label}: blocking engineering/operational work is {blocker['state']}.")
        if mode == "authorized" and blocker["production_blocking"]:
            acceptable = {"EXTERNALLY_VERIFIED", "WAIVED_WITH_AUTHORITY"} if external else {"LOCALLY_VERIFIED", "EXTERNALLY_VERIFIED"}
            if blocker["state"] not in acceptable:
                errors.append(f"{label}: not closed for authorized deployment (state={blocker['state']}).")
    return errors


def governance_report(ledger: dict[str, Any], *, root: Path = ROOT) -> tuple[list[str], list[str]]:
    """Classify privacy approval work rather than reporting a bare error total."""
    scripts = str(root / "scripts")
    if scripts not in sys.path:
        sys.path.insert(0, scripts)
    try:
        from check_data_governance import load_registry, load_schema, validate_registry
        schema = load_schema()
        issues = validate_registry(schema, load_registry(root / "docs/government/data-governance-registry.yaml"), require_approved=True)
    except Exception as exc:  # fail closed without printing data values
        return [f"Governance inventory could not be evaluated ({type(exc).__name__})."], []

    personal = [item for item in issues if item.startswith("Personal-data record has not received accountable approval:")]
    tables = [item for item in issues if "data-owner/scope/retention metadata is unresolved:" in item]
    profiles = [item for item in issues if item.startswith("Governance profile ") and "has unresolved controls:" in item]
    classified = set(personal + tables + profiles)
    unclassified = [item for item in issues if item not in classified]
    counts = {
        "personal_field_approvals": len(personal),
        "table_governance_records": len(tables),
        "governance_profiles": len(profiles),
    }
    expectations = ledger.get("governance_expectations", {})
    errors = []
    for name, count in counts.items():
        print(f"GOVERNANCE {name}: {count} pending accountable decision(s).")
        if expectations.get(name) != count:
            errors.append(f"Governance ledger count drift for {name}: ledger={expectations.get(name)}, current={count}.")
    print(f"GOVERNANCE scope: {len(schema)} mapped tables, {sum(len(columns) for columns in schema.values())} columns.")
    if unclassified:
        errors.append(f"{len(unclassified)} governance inventory/parity error(s) are not categorized as external approval work.")
    return errors, unclassified


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("candidate", "authorized"), default="candidate")
    parser.add_argument("--ledger", type=Path, default=LEDGER)
    arguments = parser.parse_args()
    try:
        ledger = load_ledger(arguments.ledger)
    except (OSError, ValueError, yaml.YAMLError) as exc:
        print(f"BLOCKER LEDGER INVALID: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2

    errors = validate_inventory(ledger)
    errors.extend(validate_ledger(ledger, mode=arguments.mode))
    governance_errors, _ = governance_report(ledger, root=ROOT)
    errors.extend(governance_errors)
    by_type = Counter(item["type"] for item in ledger["blockers"] if isinstance(item, dict))
    by_severity = Counter(
        item["severity"] for item in ledger["blockers"]
        if isinstance(item, dict) and item.get("production_blocking")
        and item.get("state") not in COMPLETED_STATES
    )
    print("BLOCKER LEDGER BY TYPE: " + ", ".join(f"{key}={by_type[key]}" for key in sorted(by_type)))
    print("OPEN PRODUCTION BLOCKERS BY SEVERITY: " + ", ".join(f"{key}={by_severity[key]}" for key in ("CRITICAL", "HIGH", "MEDIUM", "LOW")))
    for item in ledger["blockers"]:
        if isinstance(item, dict) and item.get("production_blocking") and item.get("state") not in COMPLETED_STATES:
            print(f"{item['id']} [{item['type']}/{item['severity']}/{item['state']}] owner={item['owner_role']} evidence={item['required_evidence']} — {item['title']}")
    for error in errors:
        print(f"BLOCKED: {error}", file=sys.stderr)

    active = [item for item in ledger["blockers"] if isinstance(item, dict) and item.get("production_blocking") and item.get("state") not in COMPLETED_STATES]
    if arguments.mode == "candidate" and not errors and not any(item["type"] not in EXTERNAL_TYPES for item in active):
        print("ENGINEERING PRODUCTION CANDIDATE — EXTERNAL APPROVALS REQUIRED")
        return 0
    if arguments.mode == "candidate" and not errors:
        print("ENGINEERING RELEASE CANDIDATE: PASS; external approvals remain outstanding.")
        return 0
    if arguments.mode == "authorized" and not errors:
        print("AUTHORIZED GOVERNMENT PRODUCTION DEPLOYMENT: evidence gates passed.")
        return 0
    print("NOT PRODUCTION READY: blocker ledger or evidence gate is open.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
