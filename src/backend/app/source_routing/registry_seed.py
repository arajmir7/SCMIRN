"""Deterministic, source-gated bootstrap for official service handoffs.

The JSON catalog contains only bounded facts reviewed from official primary
pages. Importing it never authorizes an agency integration or submits citizen
data. Stable UUIDv5 keys and insert-only version handling make repeated imports
idempotent; a content change requires a new catalog version.
"""
import json
import uuid
from pathlib import Path

from app.extensions import db
from app.source_routing.audit_models import AuditEvent  # noqa: F401 - register metadata
from app.source_routing.models import (
    Authority,
    GovernmentService,
    OfficialSource,
    RouteRule,
    utcnow_naive,
)


CATALOG_PATH = Path(__file__).with_name("official_source_catalog.json")
CATALOG_NAMESPACE = uuid.UUID("829b9b97-9f5a-4dae-9052-6467f8acd81b")


def _stable_id(kind, key, version):
    return str(uuid.uuid5(CATALOG_NAMESPACE, "{}:{}:{}".format(kind, key, version)))


def _by_version(model, key_field, key, version):
    return model.query.filter_by(**{key_field: key, "version": version}).first()


def _check_immutable(existing, expected, label):
    conflicts = [
        field for field, value in expected.items()
        if getattr(existing, field) != value
    ]
    if conflicts:
        raise RuntimeError(
            "Official catalog import refused: {}@{} conflicts in {}. "
            "Create a new version instead of editing an imported version.".format(
                label, expected.get("version"), ", ".join(conflicts)
            )
        )


def _load_catalog():
    with CATALOG_PATH.open("r", encoding="utf-8") as catalog_file:
        catalog = json.load(catalog_file)
    if catalog.get("catalog_version") != 1:
        raise RuntimeError("Unsupported official source catalog version.")
    return catalog


def seed_routing_registry():
    """Import reviewed sources, authorities, services, and deterministic rules."""
    catalog = _load_catalog()
    now = utcnow_naive()
    source_records = {}

    for spec in catalog["sources"]:
        source = _by_version(OfficialSource, "source_key", spec["source_key"], spec["version"])
        expected = {
            "source_key": spec["source_key"],
            "version": spec["version"],
            "authority": spec["authority"],
            "title": spec["title"],
            "source_type": spec["source_type"],
            "jurisdiction": spec["jurisdiction"],
            "canonical_url": spec["canonical_url"],
            "document_hash": spec["document_hash"],
            "verification_status": spec["verification_status"],
            "parser_version": "official-catalog-v1",
        }
        if source is None:
            supersedes_id = None
            earlier = OfficialSource.query.filter_by(source_key=spec["source_key"]).order_by(OfficialSource.version.desc()).first()
            if earlier and earlier.version < spec["version"]:
                supersedes_id = earlier.id
            source = OfficialSource(
                id=_stable_id("source", spec["source_key"], spec["version"]),
                **expected,
                retrieved_at=now,
                verified_at=now if spec["verification_status"] == "VERIFIED" else None,
                effective_from=None,
                effective_until=None,
                supersedes_id=supersedes_id,
                reviewer="SCMIRN internal source provenance review ({})".format(catalog["reviewed_on"]),
            )
            db.session.add(source)
            db.session.flush()
        else:
            _check_immutable(source, expected, "source")
        source_records[(spec["source_key"], spec["version"])] = source

    def sources_for(keys):
        records = []
        for key in keys:
            matching = [source for (source_key, _), source in source_records.items() if source_key == key]
            if not matching:
                raise RuntimeError("Official catalog refers to unknown source: " + key)
            records.append(max(matching, key=lambda source: source.version))
        return records

    authority_records = {}
    for spec in catalog["authorities"]:
        authority = _by_version(Authority, "authority_key", spec["authority_key"], spec["version"])
        authority_sources = sources_for(spec["source_keys"])
        expected = {
            "authority_key": spec["authority_key"],
            "version": spec["version"],
            "canonical_name": spec["canonical_name"],
            "authority_level": spec["authority_level"],
            "jurisdiction": spec["jurisdiction"],
            "official_source_id": authority_sources[0].id,
            "status": "ACTIVE",
        }
        if authority is None:
            authority = Authority(
                id=_stable_id("authority", spec["authority_key"], spec["version"]),
                **expected,
                created_at=now,
            )
            db.session.add(authority)
            db.session.flush()
        else:
            _check_immutable(authority, expected, "authority")
        authority_records[(spec["authority_key"], spec["version"])] = authority

    for spec in catalog["services"]:
        authority = authority_records[(spec["authority_key"], spec.get("authority_version", 1))]
        source_records_for_service = sources_for(spec["source_keys"])
        verified_sources = [source for source in source_records_for_service if source.verification_status == "VERIFIED"]
        last_verified = (
            min(source.verified_at for source in verified_sources)
            if len(verified_sources) == len(source_records_for_service) and verified_sources
            else None
        )
        expected = {
            "service_key": spec["service_key"],
            "version": spec["version"],
            "canonical_name": spec["canonical_name"],
            "description": spec["description"],
            "authority_id": authority.id,
            "department": spec["department"],
            "authority_level": spec["authority_level"],
            "jurisdiction": spec["jurisdiction"],
            "geography": spec["geography"],
            "eligibility": spec["eligibility"],
            "exclusions": spec["exclusions"],
            "issue_types": spec["issue_types"],
            "required_evidence": [],
            "recommended_evidence": [],
            "optional_evidence": [],
            "application_channel": spec["application_channel"],
            "grievance_channel": spec.get("grievance_channel"),
            "appeal_channel": None,
            "escalation_channel": None,
            "official_url": spec["official_url"],
            "integration_mode": "OFFICIAL_HANDOFF_ONLY",
            "connector_id": None,
            "identity_assurance_required": "A0",
            "official_sla": None,
            "last_verified": last_verified,
            "status": "ACTIVE",
        }
        service = _by_version(GovernmentService, "service_key", spec["service_key"], spec["version"])
        if service is None:
            service = GovernmentService(
                id=_stable_id("service", spec["service_key"], spec["version"]),
                **expected,
                created_at=now,
            )
            service.sources.extend(source_records_for_service)
            db.session.add(service)
            db.session.flush()
        else:
            _check_immutable(service, expected, "service")
            existing_source_ids = {source.id for source in service.sources}
            expected_source_ids = {source.id for source in source_records_for_service}
            if existing_source_ids != expected_source_ids:
                raise RuntimeError(
                    "Official catalog import refused: service source links changed; "
                    "create a new service version."
                )

        for rule_spec in spec["rules"]:
            rule_expected = {
                "rule_key": rule_spec["rule_key"],
                "version": spec["version"],
                "issue_type": rule_spec["issue_type"],
                "match_terms": rule_spec["match_terms"],
                "exclusion_terms": rule_spec["exclusion_terms"],
                "authority_id": authority.id,
                "service_version_id": service.id,
                "source_ids": [source.id for source in source_records_for_service],
                "priority": rule_spec["priority"],
                "status": "ACTIVE",
            }
            rule = _by_version(RouteRule, "rule_key", rule_spec["rule_key"], spec["version"])
            if rule is None:
                db.session.add(RouteRule(
                    id=_stable_id("rule", rule_spec["rule_key"], spec["version"]),
                    **rule_expected,
                    effective_from=None,
                    effective_until=None,
                    created_at=now,
                ))
            else:
                _check_immutable(rule, rule_expected, "route rule")

    db.session.commit()
