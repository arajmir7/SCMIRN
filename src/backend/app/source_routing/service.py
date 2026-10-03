"""Deterministic, source-gated citizen routing.

Free text is classified only by versioned phrase rules. It is not sent to an
LLM, retained in the database, or treated as a government filing.
"""
import hashlib
import hmac
import json
import re
import unicodedata
from datetime import timedelta
from urllib.parse import urlsplit

from sqlalchemy.exc import IntegrityError
from flask import current_app

from app.extensions import db
from app.source_routing.models import (
    Authority,
    GovernmentService,
    OfficialSource,
    RouteDecision,
    RouteRule,
    utcnow_naive,
)


RULESET_VERSION = "scmirn-jurisdiction-v1"
MODEL_VERSION = None
DECISION_RETENTION_DAYS = 30


class RoutingInputError(ValueError):
    pass


class IdempotencyConflict(ValueError):
    pass


def _normalize(value):
    return " ".join(unicodedata.normalize("NFKC", value).casefold().split())


def _contains_phrase(text, phrase):
    return re.search(r"(?<![\w])" + re.escape(_normalize(phrase)) + r"(?![\w])", text) is not None


def _effective(record, now):
    return (
        (record.effective_from is None or record.effective_from <= now)
        and (record.effective_until is None or record.effective_until > now)
    )


def _canonical_hash(value):
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _safe_url(value):
    if not isinstance(value, str):
        return False
    try:
        parsed = urlsplit(value)
        return (
            parsed.scheme == "https"
            and bool(parsed.hostname)
            and not parsed.username
            and not parsed.password
            and parsed.port in (None, 443)
        )
    except ValueError:
        return False


def _same_verified_source_host(value, sources):
    if not _safe_url(value):
        return False
    target_host = urlsplit(value).hostname.lower()
    source_hosts = {
        parsed.hostname.lower()
        for source in sources
        if _safe_url(source.canonical_url)
        for parsed in (urlsplit(source.canonical_url),)
    }
    return target_host in source_hosts


def _service_channels_match_sources(service, sources):
    """Only allow handoff URLs on the exact host of a verified source."""
    if not _same_verified_source_host(service.official_url, sources):
        return False
    urls = (service.application_channel, service.appeal_channel, service.escalation_channel)
    if any(value is not None and not _same_verified_source_host(value, sources) for value in urls):
        return False
    phone = service.grievance_channel
    if phone is not None:
        if phone.startswith("tel:"):
            if not re.fullmatch(r"tel:\+?[0-9][0-9 ().-]{2,30}", phone):
                return False
        elif not _same_verified_source_host(phone, sources):
            return False
    return True


def _geography_matches(service, state, district):
    geography = service.geography or {}
    scope = geography.get("scope")
    if scope == "national":
        return True
    states = {str(item).casefold() for item in geography.get("states", []) if isinstance(item, str)}
    districts = {str(item).casefold() for item in geography.get("districts", []) if isinstance(item, str)}

    # For non-national services, missing geography is not a wildcard. In
    # particular, district names are not globally unique and must be paired
    # with an explicitly configured, matching state.
    if not states or not state or state.strip().casefold() not in states:
        return False

    if scope == "district" and not districts:
        return False
    if districts and (not district or district.strip().casefold() not in districts):
        return False
    return True


def _source_snapshot(source):
    return {
        "source_id": source.source_key,
        "version": source.version,
        "source_type": source.source_type,
        "title": source.title,
        "authority": source.authority,
        "canonical_url": source.canonical_url,
        "document_hash": source.document_hash,
        "verification_status": source.verification_status,
        "verified_at": source.verified_at.isoformat() if source.verified_at else None,
        "reviewed_on": source.reviewed_on.isoformat() if source.reviewed_on else None,
        "verified_on": source.verified_on.isoformat() if source.verified_on else None,
    }


def classify_issue(description):
    """Extract a bounded issue type and urgency signals without generative AI."""
    normalized = _normalize(description)
    urgent_phrases = (
        "immediate danger",
        "someone is in danger now",
        "active attack",
        "being attacked now",
        "life threatening emergency",
    )
    if any(_contains_phrase(normalized, phrase) for phrase in urgent_phrases):
        return {
            "issue_type": "UNCLASSIFIED",
            "urgency": "UNASSESSED",
            "urgency_signal": "POSSIBLE_IMMEDIATE_DANGER",
            "matched_term": None,
            "urgent_human_help_required": True,
        }

    return {
        "issue_type": "UNCLASSIFIED",
        "urgency": "UNASSESSED",
        "urgency_signal": "NONE_DETECTED",
        "matched_term": None,
        "urgent_human_help_required": False,
    }


def _eligible_reviewed_sources(source_ids, now):
    """Return catalog-approved source snapshots after local metadata checks.

    This function does not fetch the government page or verify that it remains
    unchanged. A date-only review record is not live source verification.
    """
    if not source_ids:
        return []
    sources = OfficialSource.query.filter(OfficialSource.id.in_(source_ids)).all()
    if len(sources) != len(set(source_ids)):
        return []
    if any(
        source.verification_status != "VERIFIED"
        or not (source.verified_at or source.verified_on)
        or not re.fullmatch(r"[0-9a-f]{64}", source.document_hash or "")
        or not _effective(source, now)
        or not _safe_url(source.canonical_url)
        for source in sources
    ):
        return []
    return sources


def _candidate_rules(normalized_text, now):
    rules = RouteRule.query.filter_by(status="ACTIVE").all()
    matches = []
    for rule in rules:
        if not _effective(rule, now):
            continue
        if any(_contains_phrase(normalized_text, term) for term in (rule.exclusion_terms or [])):
            continue
        matched = next((term for term in (rule.match_terms or []) if _contains_phrase(normalized_text, term)), None)
        if matched is not None:
            matches.append((rule, matched))
    return sorted(matches, key=lambda entry: (-entry[0].priority, entry[0].rule_key, entry[0].version))


def _build_result(classification, outcome, explanation, *, authority=None, service=None, rule=None, sources=None):
    sources = sources or []
    result = {
        "outcome": outcome,
        "issue_type": classification["issue_type"],
        "urgency": classification["urgency"],
        "urgency_signal": classification["urgency_signal"],
        "urgent_human_help_required": classification["urgent_human_help_required"],
        "explanation": explanation,
        "route_rule_version": f"{rule.rule_key}@{rule.version}" if rule else RULESET_VERSION,
        "service_registry_version": f"{service.service_key}@{service.version}" if service else "no-active-service-match",
        "model_version": MODEL_VERSION,
        "authority": None,
        "service": None,
        "official_handoff": None,
        "submission_status": "NOT_SUBMITTED",
        "official_reference": None,
        "sources": [_source_snapshot(source) for source in sources],
    }
    if authority and service and rule:
        result["issue_type"] = rule.issue_type
        result["authority"] = {
            "authority_id": authority.authority_key,
            "name": authority.canonical_name,
            "level": authority.authority_level,
        }
        result["service"] = {
            "service_id": service.service_key,
            "version": service.version,
            "name": service.canonical_name,
            "status": service.status,
            "integration_mode": service.integration_mode,
            "official_url": service.official_url,
            "application_channel": service.application_channel,
            "grievance_channel": service.grievance_channel,
            "required_evidence": service.required_evidence or [],
            "recommended_evidence": service.recommended_evidence or [],
            "optional_evidence": service.optional_evidence or [],
        }
        if service.integration_mode == "OFFICIAL_HANDOFF_ONLY":
            result["outcome"] = "OFFICIAL_HANDOFF_ONLY"
            result["official_handoff"] = {
                "url": service.application_channel or service.official_url,
                "phone": service.grievance_channel,
                "message": "Open the official channel yourself. SCMIRN has not sent your information or created an official reference.",
            }
    return result


def resolve(description, *, state=None, district=None, consent=False, idempotency_key=None):
    if not isinstance(description, str) or not description.strip():
        raise RoutingInputError("Describe the problem before requesting a route.")
    if len(description) > 8000:
        raise RoutingInputError("The description must be 8,000 characters or fewer.")
    if not consent:
        raise RoutingInputError("Consent to process the description is required.")
    for label, value in (("state", state), ("district", district)):
        if value is not None and (not isinstance(value, str) or len(value.strip()) > 120):
            raise RoutingInputError(f"{label.title()} must be 120 characters or fewer.")
    if idempotency_key is not None and (
        not isinstance(idempotency_key, str)
        or not idempotency_key.strip()
        or len(idempotency_key) > 128
    ):
        raise RoutingInputError("Idempotency key must be 128 characters or fewer.")

    now = utcnow_naive()
    normalized = _normalize(description)
    classification = classify_issue(description)
    facts = {
        "issue_type": classification["issue_type"],
        "urgency": classification["urgency"],
        "urgency_signal": classification["urgency_signal"],
        "matched_term": classification["matched_term"],
        "geography_provided": {"state": bool(state and state.strip()), "district": bool(district and district.strip())},
        "classifier_version": RULESET_VERSION,
    }

    matches = [] if classification["urgent_human_help_required"] else _candidate_rules(normalized, now)
    selected = None
    eligible_sources = []
    if matches:
        top_priority = matches[0][0].priority
        top_matches = [match for match in matches if match[0].priority == top_priority]
        if len(top_matches) == 1:
            rule, matched_term = top_matches[0]
            service = rule.service
            authority = rule.authority
            source_ids = list(rule.source_ids or [])
            eligible_sources = _eligible_reviewed_sources(source_ids, now)
            if (
                service
                and authority
                and service.status == "ACTIVE"
                and authority.status == "ACTIVE"
                and service.authority_id == authority.id
                and _effective(service, now)
                and _effective(authority, now)
                # This resolver implements user-controlled official handoffs
                # only. Other registry modes need a separately implemented
                # and authorized connector workflow before they can route.
                and service.integration_mode == "OFFICIAL_HANDOFF_ONLY"
                and eligible_sources
                and set(source_ids).issubset({source.id for source in service.sources})
                and _service_channels_match_sources(service, eligible_sources)
                and _geography_matches(service, state, district)
            ):
                # Issue classification may identify a service category, but
                # it does not establish severity. Only a reviewed, effective
                # severity policy may assign LOW/NORMAL/HIGH/CRITICAL.
                classification.update({"issue_type": rule.issue_type, "matched_term": matched_term})
                selected = (rule, service, authority)

    if selected:
        rule, service, authority = selected
        explanation = (
            f"The description matched the deterministic rule {rule.rule_key}@{rule.version}. "
            f"The service and source versions shown below support an official handoff only. "
            "Urgency has not been assessed because no reviewed severity policy is configured."
        )
        result = _build_result(classification, "OFFICIAL_HANDOFF_ONLY", explanation, authority=authority, service=service, rule=rule, sources=eligible_sources)
        rule_id = rule.id
        authority_id = authority.id
        source_versions = [_source_snapshot(source) for source in eligible_sources]
    else:
        if classification["urgent_human_help_required"]:
            explanation = "The description contains a possible immediate-danger signal. SCMIRN cannot provide emergency response; contact local emergency services or a trusted person now. No agency route was inferred."
            outcome = "URGENT_HUMAN_HELP_REQUIRED"
        elif len(matches) > 1 and matches[0][0].priority == matches[1][0].priority:
            explanation = "More than one active rule matched with equal priority. SCMIRN abstained because the responsible authority is ambiguous."
            outcome = "JURISDICTION_AMBIGUOUS"
        else:
            explanation = "No active service rule with complete source-review metadata matched this description. SCMIRN has not inferred an authority."
            outcome = "ROUTE_UNCERTAIN"
        result = _build_result(classification, outcome, explanation)
        rule_id = None
        authority_id = None
        source_versions = []

    facts["issue_type"] = result["issue_type"]
    facts["urgency"] = result["urgency"]
    facts["urgency_signal"] = result["urgency_signal"]
    facts["matched_term"] = classification["matched_term"]
    fingerprint_key = str(current_app.config.get("SECRET_KEY") or "").encode("utf-8")
    fingerprint_input = _canonical_hash({
        "facts": facts,
        "normalized_description": normalized,
        "geography": {
            "state": _normalize(state) if state else None,
            "district": _normalize(district) if district else None,
        },
    }).encode("utf-8")
    fingerprint = hmac.new(fingerprint_key, fingerprint_input, hashlib.sha256).hexdigest()
    key_hash = hashlib.sha256(idempotency_key.encode("utf-8")).hexdigest() if idempotency_key else None

    if key_hash:
        existing = RouteDecision.query.filter_by(idempotency_key=key_hash).first()
        if existing:
            if existing.input_fingerprint != fingerprint:
                raise IdempotencyConflict("This idempotency key was already used for different facts.")
            return existing.output | {"decision_id": existing.id, "created_at": existing.created_at.isoformat(), "retention_until": existing.retention_until.isoformat()}

    decision = RouteDecision(
        idempotency_key=key_hash,
        input_fingerprint=fingerprint,
        input_facts=facts,
        route_rule_id=rule_id,
        route_rule_version=result["route_rule_version"],
        service_registry_version=result["service_registry_version"],
        source_versions=source_versions,
        model_version=MODEL_VERSION,
        output_authority_id=authority_id,
        outcome=result["outcome"],
        explanation=result["explanation"],
        output=result,
        retention_until=now + timedelta(days=DECISION_RETENTION_DAYS),
    )
    try:
        db.session.add(decision)
        db.session.flush()
        from app.source_routing.audit_chain import append_event

        append_event(
            tenant_id="public:civic-routing",
            actor_id="anonymous-citizen",
            actor_role="citizen",
            action="route.decision.created",
            object_type="route_decision",
            object_id=decision.id,
            details={
                "outcome": result["outcome"],
                "issue_type": result["issue_type"],
                "route_rule_version": result["route_rule_version"],
                "service_registry_version": result["service_registry_version"],
            },
        )
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        if key_hash:
            existing = RouteDecision.query.filter_by(idempotency_key=key_hash).first()
            if existing and existing.input_fingerprint == fingerprint:
                return existing.output | {"decision_id": existing.id, "created_at": existing.created_at.isoformat(), "retention_until": existing.retention_until.isoformat()}
        raise

    result["decision_id"] = decision.id
    result["created_at"] = decision.created_at.isoformat()
    result["retention_until"] = decision.retention_until.isoformat()
    return result


def list_services():
    now = utcnow_naive()
    services = GovernmentService.query.filter_by(
        status="ACTIVE", integration_mode="OFFICIAL_HANDOFF_ONLY"
    ).order_by(GovernmentService.service_key, GovernmentService.version.desc()).all()
    items = []
    seen = set()
    for service in services:
        if service.service_key in seen or not _effective(service, now):
            continue
        sources = list(service.sources or [])
        eligible_sources = _eligible_reviewed_sources([source.id for source in sources], now) if sources else []
        if not sources or len(eligible_sources) != len(sources) or not _service_channels_match_sources(service, eligible_sources):
            continue
        seen.add(service.service_key)
        items.append({
            "service_id": service.service_key,
            "version": service.version,
            "canonical_name": service.canonical_name,
            "description": service.description,
            "authority": service.authority.canonical_name if service.authority else None,
            "authority_level": service.authority_level,
            "jurisdiction": service.jurisdiction,
            "eligibility": service.eligibility,
            "exclusions": service.exclusions,
            "issue_types": service.issue_types,
            "required_evidence": service.required_evidence,
            "recommended_evidence": service.recommended_evidence,
            "optional_evidence": service.optional_evidence,
            "application_channel": service.application_channel,
            "grievance_channel": service.grievance_channel,
            "appeal_channel": service.appeal_channel,
            "escalation_channel": service.escalation_channel,
            "official_url": service.official_url,
            "integration_mode": service.integration_mode,
            "connector_id": service.connector_id,
            "identity_assurance_required": service.identity_assurance_required,
            "official_sla": service.official_sla,
            "source_ids": [source.source_key for source in sources],
            "sources": [_source_snapshot(source) for source in eligible_sources],
            "effective_from": service.effective_from.isoformat() if service.effective_from else None,
            "effective_until": service.effective_until.isoformat() if service.effective_until else None,
            "last_verified": service.last_verified.isoformat() if service.last_verified else None,
            "last_verified_on": service.last_verified_on.isoformat() if service.last_verified_on else None,
            "status": service.status,
        })
    return items


def check_evidence(service_key, provided_ids):
    if not isinstance(provided_ids, list) or len(provided_ids) > 100 or any(not isinstance(item, str) for item in provided_ids):
        raise RoutingInputError("Evidence item IDs must be a list of at most 100 strings.")
    service = GovernmentService.query.filter_by(service_key=service_key, status="ACTIVE").order_by(GovernmentService.version.desc()).first()
    if not service:
        return {"service_id": service_key, "status": "SERVICE_UNAVAILABLE", "requirements": [], "missing_required": []}
    sources = list(service.sources or [])
    if not sources or len(_eligible_reviewed_sources([source.id for source in sources], utcnow_naive())) != len(sources):
        return {"service_id": service_key, "status": "SOURCE_UNVERIFIED", "requirements": [], "missing_required": []}
    requirements = []
    for level, entries in (("REQUIRED", service.required_evidence), ("RECOMMENDED", service.recommended_evidence), ("OPTIONAL", service.optional_evidence)):
        for item in entries or []:
            if not isinstance(item, dict) or not item.get("evidence_id"):
                continue
            requirements.append({**item, "status": level, "provided": item["evidence_id"] in set(provided_ids)})
    missing = [item["evidence_id"] for item in requirements if item["status"] == "REQUIRED" and not item["provided"]]
    if not requirements:
        status = "UNCONFIGURED"
    else:
        status = "INCOMPLETE" if missing else "READY"
    return {"service_id": service_key, "service_version": service.version, "status": status, "requirements": requirements, "missing_required": missing}
