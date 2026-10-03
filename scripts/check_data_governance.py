#!/usr/bin/env python3
"""Verify persisted-column inventory and personal-data governance metadata."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = REPO_ROOT / "docs/government/data-governance-registry.yaml"
REQUIRED_PROFILE_FIELDS = frozenset({
    "processing_justification",
    "consent_notice_requirement",
    "processor",
    "storage",
    "region",
    "encryption",
    "authorized_roles",
    "retention",
    "deletion",
    "export",
    "correction",
    "grievance_path",
})
REQUIRED_TABLE_FIELDS = frozenset({
    "columns", "data_boundary_classification", "owner", "scope",
    "sensitivity", "retention_class",
})
PERSONAL_NAME_TOKENS = frozenset({
    "email", "phone", "password", "name", "address", "pincode", "user",
    "reporter", "citizen", "location", "lat", "lon", "lng", "session",
    "message", "response", "description", "evidence", "media", "file",
    "language", "feedback", "actor", "token", "owner", "identity",
    "consent", "state", "district",
})
PERSONAL_CONTEXT_TABLES = frozenset({
    "audit_events", "chat_logs", "documents", "issues", "route_decisions",
    "srs_audit_logs", "srs_issue_events", "srs_issues", "srs_work_orders",
    "evidence_objects", "staff_audit_events", "staff_case_events", "staff_cases",
    "staff_mfa_challenges", "staff_mfa_factors", "staff_role_grants",
    "staff_sessions", "staff_users", "user_gamification", "users",
})
CANDIDATE_EXEMPTION_REASONS = {
    "authorities.canonical_name": "Published name of an authority in the global reference catalog.",
    "blockchain_tx.contract_address": "Public infrastructure contract address, not a natural-person identifier.",
    "government_services.canonical_name": "Published service name in the global reference catalog.",
    "government_services.description": "Published general service description, not citizen supplied text.",
    "government_services.identity_assurance_required": "Published service assurance category, not a person's identity record.",
    "government_services.optional_evidence": "Published evidence category, not an uploaded citizen document.",
    "government_services.recommended_evidence": "Published evidence category, not an uploaded citizen document.",
    "government_services.required_evidence": "Published evidence category, not an uploaded citizen document.",
    "iot_assets.lat": "Infrastructure asset coordinates; separately security-sensitive, not person location data.",
    "iot_assets.lng": "Infrastructure asset coordinates; separately security-sensitive, not person location data.",
    "iot_readings.lat": "Infrastructure sensor coordinates; separately security-sensitive, not person location data.",
    "iot_readings.lng": "Infrastructure sensor coordinates; separately security-sensitive, not person location data.",
    "offices.address": "Public office address, not a citizen or employee home address.",
    "offices.lat": "Public office coordinates, not a person's location.",
    "offices.lon": "Public office coordinates, not a person's location.",
    "offices.name": "Published name of an office in the public directory.",
    "resilience_hubs.address": "Infrastructure facility address; separately security-sensitive, not personal address data.",
    "resilience_hubs.lat": "Infrastructure facility coordinates, not a person's location.",
    "resilience_hubs.lng": "Infrastructure facility coordinates, not a person's location.",
    "srs_assets.lat": "Infrastructure asset coordinates; separately security-sensitive, not person location data.",
    "srs_assets.lon": "Infrastructure asset coordinates; separately security-sensitive, not person location data.",
}


def load_registry(path: Path = REGISTRY_PATH) -> dict[str, Any]:
    with path.open(encoding="utf-8") as registry_file:
        registry = yaml.safe_load(registry_file)
    if not isinstance(registry, dict):
        raise ValueError("Data governance registry must be a YAML mapping")
    return registry


def load_schema() -> dict[str, set[str]]:
    """Load all mapped SQLAlchemy tables without opening a database connection."""
    backend_root = REPO_ROOT / "src/backend"
    if str(backend_root) not in sys.path:
        sys.path.insert(0, str(backend_root))
    from app.extensions import db
    import app.infrastructure.database.models  # noqa: F401
    import app.source_routing.audit_models  # noqa: F401
    import app.source_routing.models  # noqa: F401
    import app.staff_auth.models  # noqa: F401

    return {
        str(table_name): {str(column.name) for column in table.columns}
        for table_name, table in db.metadata.tables.items()
    }


def _field_tokens(field_name: str) -> set[str]:
    return set(field_name.lower().split("_"))


def _contains_unresolved_marker(value: Any) -> bool:
    if isinstance(value, list):
        return any(_contains_unresolved_marker(item) for item in value)
    if not isinstance(value, str):
        return value in (None, "", [])
    normalized = value.upper()
    return any(marker in normalized for marker in (
        "UNASSESSED", "UNCONFIGURED", "UNVERIFIED", "NOT_APPROVED",
        "NOT_IMPLEMENTED", "NOT_CONFIGURED", "UNASSIGNED", "REVIEW_REQUIRED",
        "PARTIAL_OR_UNVERIFIED", "DEPLOYMENT_NOT_VERIFIED",
    ))


def _candidate_personal_fields(schema: dict[str, set[str]]) -> set[str]:
    candidates = {
        f"{table}.{column}"
        for table, columns in schema.items()
        for column in columns
        if _field_tokens(column).intersection(PERSONAL_NAME_TOKENS)
    }
    # These tables hold user/staff supplied content, case-linked events, or
    # security identities. Every present field is reviewed as potentially
    # personal or linkable, including opaque JSON and derived values.
    candidates.update(
        f"{table}.{column}"
        for table in PERSONAL_CONTEXT_TABLES.intersection(schema)
        for column in schema[table]
    )
    # A routing decision can be linked to a requester even when a column name
    # is an opaque fingerprint or derived result rather than a direct identifier.
    candidates.update({
        f"route_decisions.{column}"
        for column in ("idempotency_key", "input_fingerprint", "input_facts", "explanation", "output")
        if column in schema.get("route_decisions", set())
    })
    candidates.update({
        f"documents.{column}"
        for column in ("title", "template_data", "file_path")
        if column in schema.get("documents", set())
    })
    return candidates


def validate_registry(
    schema: dict[str, set[str]],
    registry: dict[str, Any],
    *,
    require_approved: bool = False,
) -> list[str]:
    """Return schema drift and missing/invalid personal-field governance errors."""
    issues: list[str] = []
    tables = registry.get("tables")
    profiles = registry.get("profiles")
    personal_fields = registry.get("personal_fields")
    nonpersonal_fields = registry.get("nonpersonal_fields")
    exemptions = registry.get("candidate_exemptions")
    if not all(isinstance(value, dict) for value in (tables, profiles, personal_fields, nonpersonal_fields, exemptions)):
        return ["Registry must define tables, profiles, personal_fields, nonpersonal_fields, and candidate_exemptions mappings"]

    actual_tables = set(schema)
    recorded_tables = set(tables)
    for table in sorted(actual_tables - recorded_tables):
        issues.append(f"Mapped table is missing from the schema inventory: {table}")
    for table in sorted(recorded_tables - actual_tables):
        issues.append(f"Registry table is not mapped by SQLAlchemy: {table}")
    for table in sorted(actual_tables & recorded_tables):
        table_record = tables[table]
        if not isinstance(table_record, dict):
            issues.append(f"{table} data governance record must be a mapping")
            continue
        missing_table_fields = sorted(REQUIRED_TABLE_FIELDS - set(table_record))
        empty_table_fields = sorted(
            key for key in REQUIRED_TABLE_FIELDS - {"columns"}
            if table_record.get(key) in (None, "", [], "UNASSESSED")
        )
        if missing_table_fields or empty_table_fields:
            issues.append(f"{table} data governance record is incomplete (missing={missing_table_fields}, unassessed={empty_table_fields})")
        if require_approved:
            unresolved_table_fields = sorted(
                key for key in REQUIRED_TABLE_FIELDS - {"columns"}
                if _contains_unresolved_marker(table_record.get(key))
            )
            if unresolved_table_fields:
                issues.append(f"{table} data-owner/scope/retention metadata is unresolved: {unresolved_table_fields}")
        columns = table_record.get("columns")
        if not isinstance(columns, list) or any(not isinstance(column, str) for column in columns):
            issues.append(f"{table} must record its mapped columns as a string list")
            continue
        if len(columns) != len(set(columns)):
            issues.append(f"{table} has duplicate column names in the schema inventory")
        if set(columns) != schema[table]:
            missing = sorted(schema[table] - set(columns))
            stale = sorted(set(columns) - schema[table])
            issues.append(f"{table} column inventory differs (unrecorded={missing}, stale={stale})")

    for profile_name, profile in profiles.items():
        if not isinstance(profile, dict):
            issues.append(f"Governance profile {profile_name} must be a mapping")
            continue
        missing = sorted(REQUIRED_PROFILE_FIELDS - set(profile))
        empty = sorted(key for key in REQUIRED_PROFILE_FIELDS & set(profile) if profile[key] in (None, "", []))
        if missing or empty:
            issues.append(f"Governance profile {profile_name} is incomplete (missing={missing}, empty={empty})")
        elif require_approved:
            unresolved_profile_fields = sorted(
                key for key in REQUIRED_PROFILE_FIELDS
                if _contains_unresolved_marker(profile[key])
            )
            if unresolved_profile_fields:
                issues.append(f"Governance profile {profile_name} has unresolved controls: {unresolved_profile_fields}")

    candidate_fields = _candidate_personal_fields(schema)
    recorded_fields = set(personal_fields)
    nonpersonal_recorded_fields = set(nonpersonal_fields)
    mapped_fields = {f"{table}.{column}" for table, columns in schema.items() for column in columns}
    exemption_fields = set(exemptions)
    for field in sorted(candidate_fields - recorded_fields - exemption_fields):
        issues.append(f"Candidate personal-data field lacks a personal-data record or documented exemption: {field}")
    for field in sorted(mapped_fields - recorded_fields - nonpersonal_recorded_fields):
        issues.append(f"Mapped field lacks a data-governance record: {field}")
    for field in sorted(recorded_fields & nonpersonal_recorded_fields):
        issues.append(f"Field cannot be both personal and non-personal: {field}")
    for field in sorted((recorded_fields | nonpersonal_recorded_fields) - mapped_fields):
        issues.append(f"Personal-data registry field is not a mapped column: {field}")
    for field in sorted(exemption_fields - nonpersonal_recorded_fields):
        issues.append(f"Candidate exemption needs a non-personal field record: {field}")
    for field in sorted(exemption_fields - candidate_fields):
        issues.append(f"Candidate exemption is no longer needed or has an invalid field: {field}")

    for field, entry in personal_fields.items():
        if not isinstance(entry, dict):
            issues.append(f"Personal-data record must be a mapping: {field}")
            continue
        missing = {"classification", "purpose", "profile", "status"} - set(entry)
        if missing:
            issues.append(f"Personal-data record is missing fields {sorted(missing)}: {field}")
            continue
        profile_name = entry["profile"]
        profile = profiles.get(profile_name)
        if profile is None:
            issues.append(f"Personal-data record refers to an unknown profile {profile_name}: {field}")
        if not entry["classification"] or not entry["purpose"]:
            issues.append(f"Personal-data record classification and purpose must be explicit: {field}")
        if entry.get("status") not in {"UNREVIEWED", "INVENTORIED", "APPROVED"}:
            issues.append(f"Personal-data record status must be UNREVIEWED, INVENTORIED, or APPROVED: {field}")
        elif entry["status"] == "UNREVIEWED":
            issues.append(f"Personal-data record requires engineering inventory before CI can pass: {field}")
        elif require_approved and entry["status"] != "APPROVED":
            issues.append(f"Personal-data record has not received accountable approval: {field}")

    for field, entry in nonpersonal_fields.items():
        if not isinstance(entry, dict):
            issues.append(f"Non-personal field record must be a mapping: {field}")
            continue
        if not isinstance(entry.get("reason"), str) or not entry["reason"].strip():
            issues.append(f"Non-personal field record needs a classification reason: {field}")
        if entry.get("status") not in {"UNREVIEWED", "REVIEWED"}:
            issues.append(f"Non-personal field status must be UNREVIEWED or REVIEWED: {field}")
        elif entry["status"] == "UNREVIEWED":
            issues.append(f"Non-personal field needs explicit classification before CI can pass: {field}")
        elif require_approved and entry["status"] != "REVIEWED":
            issues.append(f"Non-personal field classification has not been reviewed: {field}")

    for field, entry in exemptions.items():
        if not isinstance(entry, dict) or not isinstance(entry.get("reason"), str) or not entry["reason"].strip():
            issues.append(f"Candidate exemption needs a documented reason: {field}")

    return issues


def _initial_classification(field: str) -> str:
    column = field.split(".", 1)[1]
    tokens = set(column.split("_"))
    if "password" in tokens or column in {
        "secret_ciphertext", "token_hash", "enrollment_token_hash",
        "csrf_hash", "session_hash",
    }:
        return "AUTHENTICATION_OR_SESSION_SECRET"
    if tokens.intersection({"lat", "lon", "lng", "pincode", "district", "state", "location", "address", "ward"}):
        return "LOCATION_OR_GEOGRAPHIC_DATA"
    if tokens.intersection({"phone", "email", "name"}):
        return "DIRECT_IDENTIFIER_OR_CONTACT_DATA"
    if tokens.intersection({"message", "response", "description", "evidence", "media", "content", "notes", "details", "template", "file"}):
        return "USER_SUPPLIED_OR_DOCUMENT_CONTENT"
    return "LINKED_PERSONAL_OR_OPERATIONAL_DATA"


def refresh_registry(schema: dict[str, set[str]], existing: dict[str, Any] | None = None) -> dict[str, Any]:
    """Refresh exact schema inventory and add new candidates as unreviewed.

    This helper never promotes a field to approved and preserves existing
    field-specific review metadata. Refreshing therefore exposes new data
    without silently authorizing its purpose, storage, or use.
    """
    profile_name = "unreviewed_personal_data"
    profile = (existing or {}).get("profiles", {}).get(profile_name, {
        "processing_justification": "UNASSESSED_REQUIRES_ACCOUNTABLE_PRIVACY_AND_LEGAL_REVIEW",
        "consent_notice_requirement": "UNASSESSED_REQUIRES_NOTICE_AND_CONSENT_REVIEW",
        "processor": "DEPLOYMENT_PROCESSOR_UNCONFIGURED",
        "storage": "APPLICATION_DATABASE_OR_LEGACY_STORE_DEPLOYMENT_NOT_VERIFIED",
        "region": "UNCONFIGURED",
        "encryption": "DEPLOYMENT_AT_REST_CONTROLS_NOT_VERIFIED",
        "authorized_roles": ["NOT_APPROVED"],
        "retention": "UNCONFIGURED_OR_NOT_ENFORCED_FOR_LEGACY_DATA",
        "deletion": "PARTIAL_OR_UNVERIFIED; route CLI is not a production scheduler",
        "export": "NOT_IMPLEMENTED",
        "correction": "NOT_IMPLEMENTED",
        "grievance_path": "UNCONFIGURED",
    })
    personal_fields = dict((existing or {}).get("personal_fields", {}))
    exemptions = dict((existing or {}).get("candidate_exemptions", {}))
    nonpersonal_fields = dict((existing or {}).get("nonpersonal_fields", {}))
    candidates = _candidate_personal_fields(schema)
    for field, reason in CANDIDATE_EXEMPTION_REASONS.items():
        if field in candidates:
            exemptions.setdefault(field, {"reason": reason})
            nonpersonal_fields.setdefault(field, {
                "classification": "ENGINEERING_CLASSIFIED_NON_PERSONAL_CANDIDATE",
                "reason": reason,
                "status": "REVIEWED",
            })
    for field in sorted(candidates - set(exemptions)):
        personal_fields.setdefault(field, {
            "classification": _initial_classification(field),
            "purpose": "UNASSESSED_REQUIRES_ACCOUNTABLE_REVIEW",
            "profile": profile_name,
            "status": "UNREVIEWED",
        })
        existing_nonpersonal = nonpersonal_fields.get(field)
        if isinstance(existing_nonpersonal, dict) and existing_nonpersonal.get("status") == "UNREVIEWED":
            nonpersonal_fields.pop(field, None)
    mapped_fields = {f"{table}.{column}" for table, columns in schema.items() for column in columns}
    for field in sorted(mapped_fields - set(personal_fields) - set(nonpersonal_fields)):
        nonpersonal_fields[field] = {
            "classification": "UNASSESSED",
            "reason": "No personal-data name/context heuristic matched; accountable classification is still required.",
            "status": "UNREVIEWED",
        }
    existing_tables = (existing or {}).get("tables", {})
    tables = {}
    for table, columns in sorted(schema.items()):
        metadata = dict(existing_tables.get(table, {})) if isinstance(existing_tables.get(table), dict) else {}
        metadata["columns"] = sorted(columns)
        metadata.setdefault("data_boundary_classification", "UNASSESSED")
        metadata.setdefault("owner", "OWNER_UNASSIGNED")
        metadata.setdefault("scope", "UNASSESSED")
        metadata.setdefault("sensitivity", "UNASSESSED")
        metadata.setdefault("retention_class", "UNCONFIGURED")
        tables[table] = metadata
    return {
        "version": 1,
        "status": "ENGINEERING_INVENTORY_ONLY_NOT_A_LEGAL_BASIS_OR_DPDP_COMPLIANCE_CLAIM",
        "tables": tables,
        "profiles": {profile_name: profile},
        "personal_fields": dict(sorted(personal_fields.items())),
        "nonpersonal_fields": dict(sorted(nonpersonal_fields.items())),
        "candidate_exemptions": dict(sorted(exemptions.items())),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registry", type=Path, default=REGISTRY_PATH)
    parser.add_argument(
        "--refresh-inventory", action="store_true",
        help="Refresh mapped columns and register new candidate fields as UNREVIEWED.",
    )
    parser.add_argument(
        "--require-approved", action="store_true",
        help="Fail while any personal-data record lacks accountable approval.",
    )
    arguments = parser.parse_args()
    schema = load_schema()
    if arguments.refresh_inventory:
        try:
            existing = load_registry(arguments.registry) if arguments.registry.exists() else None
        except ValueError as exc:
            parser.error(str(exc))
        refreshed = refresh_registry(schema, existing)
        arguments.registry.parent.mkdir(parents=True, exist_ok=True)
        with arguments.registry.open("w", encoding="utf-8") as registry_file:
            registry_file.write(
                "# Generated inventory. New personal-data candidates start UNREVIEWED.\n"
                "# This registry is not a legal basis or DPDP compliance claim.\n"
            )
            yaml.safe_dump(refreshed, registry_file, sort_keys=False, allow_unicode=True, width=100)
        print(f"Refreshed data governance inventory: {arguments.registry}")
        return 0
    registry = load_registry(arguments.registry)
    issues = validate_registry(schema, registry, require_approved=arguments.require_approved)
    if issues:
        for issue in issues:
            print(f"ERROR: {issue}", file=sys.stderr)
        return 1
    candidate_count = len(_candidate_personal_fields(schema))
    print(
        f"Data governance schema parity passed: {len(schema)} mapped tables, "
        f"{sum(map(len, schema.values()))} columns, {candidate_count} candidate fields are registered or explicitly exempted."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
