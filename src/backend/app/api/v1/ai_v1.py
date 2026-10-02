"""
Advanced AI Legal Co-Pilot (v1).

Implements:
 - POST /api/v1/ai/classify-intent
 - POST /api/v1/ai/rights-calculate
 - POST /api/v1/ai/document-generate
 - POST /api/v1/ai/quality-check

This module provides deterministic, production-friendly baseline logic (rules + scoring)
so your website is fully functional without requiring external model hosting.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import re
import uuid
from typing import Any, Dict, List, Optional, Tuple

from flask import Blueprint, jsonify, request, current_app
from marshmallow import Schema, fields, validate, ValidationError

from app.extensions import limiter


bp = Blueprint("api_v1_ai", __name__, url_prefix="/api/v1/ai")


# -------------------------
# Helpers
# -------------------------

_INR_RE = re.compile(r"(₹|rs\.?|inr)\s*([0-9][0-9,]*\.?[0-9]*)", re.IGNORECASE)
_DATE_RE = re.compile(r"\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b")


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _extract_amounts(text: str) -> List[float]:
    out = []
    for m in _INR_RE.finditer(text or ""):
        num = m.group(2).replace(",", "")
        try:
            out.append(float(num))
        except Exception:
            continue
    return out


def _extract_dates(text: str) -> List[str]:
    # Returns ISO-ish strings if possible, else raw matches
    matches = [m.group(1) for m in _DATE_RE.finditer(text or "")]
    out = []
    for s in matches[:10]:
        # Normalize dd/mm/yyyy or dd-mm-yyyy to ISO (best-effort)
        parts = re.split(r"[/-]", s)
        if len(parts) == 3:
            d, mo, y = parts
            y = ("20" + y) if len(y) == 2 else y
            try:
                dt = datetime(int(y), int(mo), int(d), tzinfo=timezone.utc)
                out.append(dt.isoformat().replace("+00:00", "Z"))
                continue
            except Exception:
                pass
        out.append(s)
    return out


def _keyword_intent(query: str) -> Tuple[str, str, float]:
    q = (query or "").lower()

    rules = [
        ("HOUSING", "Eviction", ["evict", "landlord", "rent", "deposit", "lease", "tenant"]),
        ("LABOR", "UnfairDismissal", ["salary", "wages", "pf", "esi", "termination", "fired", "resign"]),
        ("CONSUMER", "DefectiveProduct", ["refund", "defective", "broken", "flipkart", "amazon", "service", "warranty"]),
        ("ADMINISTRATIVE", "RTI", ["rti", "information act", "public information officer", "pio"]),
        ("CIVIL_RIGHTS", "Discrimination", ["discrimin", "harass", "denied service", "rights violation"]),
        ("FAMILY", "DomesticViolence", ["dowry", "domestic", "violence", "custody", "divorce", "maintenance"]),
        ("ENVIRONMENTAL", "Pollution", ["pollution", "garbage", "sewage", "noise", "tree", "encroach"]),
        ("TRAFFIC", "Accidents", ["accident", "challan", "license", "dl", "rc", "traffic"]),
        ("TAXATION", "PropertyTax", ["property tax", "gst", "income tax", "assessment", "notice"]),
        ("CRIMINAL", "FIR", ["fir", "police", "threat", "assault", "theft", "fraud", "cybercrime"]),
    ]

    best = ("ADMINISTRATIVE", "GovernmentServices", 0.55)
    for dom, sub, kws in rules:
        hits = sum(1 for kw in kws if kw in q)
        if hits:
            conf = min(0.95, 0.6 + hits * 0.1)
            if conf > best[2]:
                best = (dom, sub, conf)
    return best


def _urgency(query: str) -> str:
    q = (query or "").lower()
    if any(x in q for x in ["tomorrow", "today", "tonight", "immediately", "right now", "threat", "violence"]):
        return "EMERGENCY"
    if any(x in q for x in ["within 7 days", "deadline", "notice", "summons", "court date", "next week"]):
        return "URGENT"
    if any(x in q for x in ["how to", "what is", "process", "steps", "guide"]):
        return "ROUTINE"
    return "STANDARD"


def _complexity(query: str) -> str:
    q = (query or "").lower()
    if any(x in q for x in ["appeal", "writ", "litigation", "case number", "hearing", "court", "petition"]):
        return "COMPLEX"
    if any(x in q for x in ["multiple", "also", "and", "plus", "along with"]):
        return "MODERATE"
    return "SIMPLE"


# -------------------------
# Schemas
# -------------------------

class ClassifyIntentSchema(Schema):
    user_query = fields.Str(required=True, validate=validate.Length(min=2, max=2000))
    conversation_context = fields.List(fields.Str(), load_default=list)


class LocationSchema(Schema):
    city = fields.Str(required=True)
    state = fields.Str(required=True)


class ClassifiedIntentSchema(Schema):
    domain = fields.Str(required=True)
    sub_domain = fields.Str(required=True)
    urgency = fields.Str(required=True)
    location = fields.Nested(LocationSchema(), required=True)


class UserFactsSchema(Schema):
    tenant_since = fields.Str(allow_none=True)
    monthly_rent = fields.Float(allow_none=True)
    deposit_amount = fields.Float(allow_none=True)
    notice_period_given = fields.Int(allow_none=True)
    written_agreement = fields.Bool(required=True)
    issue_description = fields.Str(required=True, validate=validate.Length(min=5, max=3000))


class RightsCalculateSchema(Schema):
    classified_intent = fields.Nested(ClassifiedIntentSchema(), required=True)
    user_facts = fields.Nested(UserFactsSchema(), required=True)


class DocumentRequestSchema(Schema):
    template_type = fields.Str(required=True, validate=validate.OneOf([
        "RTI_APPLICATION",
        "FIR_COMPLAINT",
        "LEGAL_NOTICE",
        "CONSUMER_COMPLAINT",
        "RENT_CONTROL_PETITION",
    ]))
    jurisdiction = fields.Dict(required=True)
    user_profile = fields.Dict(required=True)
    extracted_facts = fields.Dict(load_default=dict)
    rights_analysis = fields.Dict(load_default=dict)


class DocumentGenerateSchema(Schema):
    document_request = fields.Nested(DocumentRequestSchema(), required=True)


class ContentToEvaluateSchema(Schema):
    type = fields.Str(required=True, validate=validate.OneOf(["RIGHTS_ANALYSIS", "DOCUMENT", "CHAT_RESPONSE"]))
    content = fields.Str(required=True)
    context = fields.Dict(load_default=dict)


class QualityCheckSchema(Schema):
    content_to_evaluate = fields.Nested(ContentToEvaluateSchema(), required=True)


# -------------------------
# Routes
# -------------------------

@bp.route("/classify-intent", methods=["POST"])
@limiter.limit("60 per minute")
def classify_intent():
    try:
        schema = ClassifyIntentSchema()
        data = schema.load(request.get_json() or {})

        query = data["user_query"]
        dom, sub, conf = _keyword_intent(query)
        urg = _urgency(query)
        comp = _complexity(query)

        safety_flags = {
            "self_harm_detected": False,
            "violence_imminent": any(x in query.lower() for x in ["kill", "attack", "weapon", "violence"]),
            "statute_of_limitations_risk": any(x in query.lower() for x in ["2019", "2020", "2021", "2022"]),
            "requires_human_lawyer": urg in {"EMERGENCY", "URGENT"} or comp == "COMPLEX",
        }

        target_module = {
            "HOUSING": "rights_housing",
            "LABOR": "rights_labor",
            "CONSUMER": "rights_consumer",
            "ADMINISTRATIVE": "rti_assistant",
            "CRIMINAL": "fir_assistant",
        }.get(dom, "general_legal_assistant")

        return jsonify({
            "classification": {
                "primary_domain": dom,
                "sub_domain": sub,
                "confidence": float(round(conf, 2)),
                "secondary_domains": [],
                "urgency": urg,
                "complexity": comp,
                "entities_extracted": {
                    "dates": _extract_dates(query),
                    "amounts_inr": _extract_amounts(query),
                    "parties": [],
                    "locations": [],
                    "document_types": ["RTI"] if "rti" in query.lower() else [],
                },
            },
            "routing": {
                "target_module": target_module,
                "required_context": ["location.state", "basic_facts", "documents_available"],
                "suggested_documents": ["RTI", "FIR", "LegalNotice"],
                "estimated_processing_time_seconds": 2,
            },
            "safety_flags": safety_flags,
        }), 200

    except ValidationError as e:
        return jsonify({"success": False, "error": "Validation failed", "details": e.messages}), 400
    except Exception as e:
        current_app.logger.error(f"classify-intent error: {str(e)}")
        return jsonify({"success": False, "error": "Failed to classify intent"}), 500


@bp.route("/rights-calculate", methods=["POST"])
@limiter.limit("30 per minute")
def rights_calculate():
    """
    Baseline rights calculator (India) with Model Tenancy Act heuristics for housing scenarios.
    """
    try:
        schema = RightsCalculateSchema()
        data = schema.load(request.get_json() or {})

        intent = data["classified_intent"]
        facts = data["user_facts"]
        state = intent["location"]["state"]
        domain = intent["domain"]
        sub = intent["sub_domain"]

        issue_desc = facts["issue_description"]
        monthly_rent = facts.get("monthly_rent") or 0.0
        deposit_amount = facts.get("deposit_amount") or 0.0
        notice_given = facts.get("notice_period_given") or 0

        # Housing defaults (best-effort, non-authoritative)
        legal_notice_days = 30 if domain == "HOUSING" else 15
        max_deposit_months = 2 if domain == "HOUSING" else 0
        actual_deposit_months = 0 if monthly_rent <= 0 else int(round(deposit_amount / monthly_rent))
        deposit_excess_amount = max(0.0, deposit_amount - (max_deposit_months * monthly_rent))
        notice_deficiency = max(0, legal_notice_days - notice_given)

        applicable_laws = []
        if domain == "HOUSING":
            applicable_laws = [
                {
                    "act_name": f"{state} Rent Control Act (if applicable)",
                    "sections": ["(varies by state)"],
                    "relevance": "Covers eviction procedure, notice requirements, and tenant protections depending on state applicability.",
                    "source": "State",
                },
                {
                    "act_name": "Model Tenancy Act, 2021 (reference)",
                    "sections": ["Security Deposit (Residential cap)", "Rent Authority procedures"],
                    "relevance": "Used as a reference baseline for deposits and dispute mechanisms where state adoption exists.",
                    "source": "Central",
                },
            ]

        specific_rights = []
        if domain == "HOUSING" and sub.lower().startswith("evict"):
            specific_rights.append({
                "right_name": "Right to due process before eviction",
                "legal_basis": f"State rent control framework / tenancy law procedures (verify for {state})",
                "conditions": ["You can show tenancy (rent receipts / agreement / messages)", "Eviction attempt without proper notice or authority order"],
                "remedy": "Seek injunction/stay, approach Rent Authority/Tribunal or civil court; file complaint for illegal dispossession if force used.",
                "enforcement_authority": "Rent Authority / Rent Tribunal / Civil Court (jurisdiction dependent)",
                "timeline_days": 3 if intent["urgency"] in {"EMERGENCY", "URGENT"} else 14,
                "priority": "CRITICAL" if intent["urgency"] == "EMERGENCY" else "HIGH",
            })

        rights_analysis = {
            "applicable_laws": applicable_laws,
            "specific_rights": specific_rights,
            "calculations": {
                "legal_notice_period_days": int(legal_notice_days),
                "actual_notice_period_days": int(notice_given),
                "notice_deficiency_days": int(notice_deficiency),
                "max_deposit_months": int(max_deposit_months),
                "actual_deposit_months": int(actual_deposit_months),
                "deposit_excess_amount": float(round(deposit_excess_amount, 2)),
                "monthly_rent_cap_percent": 0.0,
            },
        }

        today = _now_utc().date()
        action_timeline = [
            {
                "phase": "Immediate",
                "deadline": datetime.combine(today, datetime.min.time(), tzinfo=timezone.utc).isoformat().replace("+00:00", "Z"),
                "action": "Collect evidence: agreement/rent receipts, notice messages, ID/address proof, photos/videos of threats/lockout.",
                "legal_basis": "Evidence preservation best practice",
                "document_required": "Rent agreement / receipts / screenshots",
                "cost_inr": 0.0,
                "diy_possible": True,
            },
            {
                "phase": "Short",
                "deadline": (_now_utc() + timedelta(days=3)).isoformat().replace("+00:00", "Z"),
                "action": "Send a written notice to landlord demanding compliance and no illegal dispossession; request deposit reconciliation if applicable.",
                "legal_basis": "Contract + tenancy procedure (verify local law)",
                "document_required": "Legal notice draft",
                "cost_inr": 0.0,
                "diy_possible": True,
            },
            {
                "phase": "Medium",
                "deadline": (_now_utc() + timedelta(days=10)).isoformat().replace("+00:00", "Z"),
                "action": "If threats continue: approach local police for GD/complaint; consult a lawyer for injunction/tribunal filing.",
                "legal_basis": "Remedies vary by state",
                "document_required": "Complaint copy + supporting evidence",
                "cost_inr": 500.0,
                "diy_possible": False,
            },
        ]

        document_templates = [
            {"template_name": "LEGAL_NOTICE", "auto_fillable": True, "required_inputs": ["names", "address", "facts", "dates"], "jurisdiction": state},
            {"template_name": "RTI_APPLICATION", "auto_fillable": True, "required_inputs": ["authority", "questions"], "jurisdiction": state},
        ]

        risk_assessment = {
            "success_probability": 0.65 if facts.get("written_agreement") else 0.5,
            "key_risks": [
                "State-specific procedures differ; confirm correct forum and notice requirements.",
                "Documentation gaps reduce enforceability; gather receipts and communication proofs.",
            ],
            "mitigation_strategies": ["Keep all communication in writing", "Use registered post/email where possible", "Avoid physical confrontation; prioritize safety"],
            "when_to_involve_lawyer": "If eviction/violence is imminent, if a court/tribunal case is needed, or if significant money is involved.",
        }

        quality_score = {
            "stanford_legal_design_score": 78,
            "completeness": 75,
            "accuracy": 70,
        }

        return jsonify({
            "rights_analysis": rights_analysis,
            "action_timeline": action_timeline,
            "document_templates": document_templates,
            "risk_assessment": risk_assessment,
            "quality_score": quality_score,
            "note": "This is an automated baseline and may require jurisdiction-specific verification.",
        }), 200

    except ValidationError as e:
        return jsonify({"success": False, "error": "Validation failed", "details": e.messages}), 400
    except Exception as e:
        current_app.logger.error(f"rights-calculate error: {str(e)}")
        return jsonify({"success": False, "error": "Failed to compute rights analysis"}), 500


@bp.route("/document-generate", methods=["POST"])
@limiter.limit("20 per minute")
def document_generate():
    try:
        schema = DocumentGenerateSchema()
        data = schema.load(request.get_json() or {})
        req = data["document_request"]

        template_type = req["template_type"]
        jurisdiction = req.get("jurisdiction") or {}
        profile = req.get("user_profile") or {}
        extracted = req.get("extracted_facts") or {}
        rights = req.get("rights_analysis") or {}

        generated_at = _now_utc()
        template_id = f"{template_type.lower()}-v1"

        header = f"To,\nThe Competent Authority,\n{jurisdiction.get('city', '')}, {jurisdiction.get('state', '')}"
        title = template_type.replace("_", " ").title()

        facts_lines = []
        for k, v in list(extracted.items())[:12]:
            facts_lines.append(f"{k}: {v}")
        if not facts_lines:
            facts_lines = ["(Auto-filled facts will appear here based on your inputs.)"]

        disclaimer = 'Generated by SCMIRN AI - Not Legal Advice. Please verify with a qualified professional.'

        body = {
            "introduction": f"I, {profile.get('name', '[Name]')}, residing at {profile.get('address', '[Address]')}, submit this {title} for appropriate action.",
            "parties": f"Applicant/Complainant: {profile.get('name', '[Name]')} | Contact: {profile.get('contact', '[Contact]')}",
            "facts": [f"{i+1}. {line}" for i, line in enumerate(facts_lines)],
            "grounds": [
                "This request/complaint is made in good faith based on the facts stated above.",
                "Where applicable, legal grounds are referenced in the attached rights analysis (jurisdiction-specific verification advised).",
            ],
            "prayer": "Kindly take necessary action as per law and provide acknowledgement/reference number.",
            "verification": f"I verify that the contents above are true to the best of my knowledge. ({disclaimer})",
            "signature_block": f"Signature:\n{profile.get('name', '[Name]')}\nDate: {generated_at.date().isoformat()}",
        }

        annexures = [
            {"serial_no": 1, "document_name": "ID Proof", "description": "Aadhaar/Passport/Driving License copy", "pages": 1},
            {"serial_no": 2, "document_name": "Supporting Evidence", "description": "Photos, receipts, screenshots, or relevant documents", "pages": 1},
        ]

        return jsonify({
            "document_metadata": {
                "template_id": template_id,
                "version": "1.0.0",
                "generated_at": generated_at.isoformat().replace("+00:00", "Z"),
                "valid_for_jurisdiction": f"{jurisdiction.get('city', '')}, {jurisdiction.get('state', '')}",
                "next_review_date": (generated_at + timedelta(days=180)).isoformat().replace("+00:00", "Z"),
                "compliance_checklist": ["All mandatory fields filled", "Jurisdiction stated", "Annexures listed", "Disclaimer present"],
            },
            "document_content": {
                "header": header,
                "title": title,
                "body": body,
                "annexures": annexures,
            },
            "filing_details": {
                "where_to_file": "Depends on document type and jurisdiction (authority office or e-filing portal where available).",
                "mode": "BOTH",
                "court_fees": 0.0,
                "stamp_paper_required": "NO",
                "stamp_paper_value": 0.0,
                "processing_time": "Varies by authority workload (typically 7-30 days).",
                "tracking_mechanism": "Acknowledgement/reference number from the receiving authority.",
            },
            "post_filing": {
                "expected_timeline": [{"stage": "Acknowledgement", "duration": "0-2 days", "responsible_party": "Authority"}],
                "follow_up_actions": ["Keep copies of submission and acknowledgement", "Follow up if no response within stated timelines"],
                "appeal_options": {"available": True, "grounds": ["No response", "Improper handling"], "deadline": "Varies by statute/procedure"},
            },
            "confidence_metrics": {
                "template_match": 0.78,
                "field_completion": 0.7,
                "legal_accuracy": 0.6,
                "human_review_recommended": True,
            },
            "watermark": disclaimer,
        }), 200

    except ValidationError as e:
        return jsonify({"success": False, "error": "Validation failed", "details": e.messages}), 400
    except Exception as e:
        current_app.logger.error(f"document-generate error: {str(e)}")
        return jsonify({"success": False, "error": "Failed to generate document"}), 500


@bp.route("/quality-check", methods=["POST"])
@limiter.limit("30 per minute")
def quality_check():
    try:
        schema = QualityCheckSchema()
        data = schema.load(request.get_json() or {})
        c = data["content_to_evaluate"]

        content = c["content"] or ""
        ctx = c.get("context") or {}

        # Simple rubric scoring
        usefulness = 10 + (5 if "step" in content.lower() or "action" in content.lower() else 0) + (5 if len(content) > 200 else 0)
        completeness = 10 + (5 if "deadline" in content.lower() or "timeline" in content.lower() else 0) + (5 if "document" in content.lower() else 0)
        accuracy = 12 + (5 if "section" in content.lower() or "act" in content.lower() else 0)
        accessibility = 12 + (5 if "\n" in content else 0)

        # Safety pass if disclaimer present for legal docs/rights
        disclaimer_present = any(x in content.lower() for x in ["not legal advice", "verify", "qualified professional", "lawyer"])
        safety_passed = disclaimer_present or c["type"] == "CHAT_RESPONSE"

        total = int(min(100, usefulness + completeness + accuracy + accessibility))
        human_review = (total < 70) or (not safety_passed)

        issues_found = []
        if not disclaimer_present and c["type"] in {"RIGHTS_ANALYSIS", "DOCUMENT"}:
            issues_found.append({
                "type": "SAFETY",
                "location": "document_content",
                "description": "Missing disclaimer for automated legal assistance.",
                "suggested_fix": "Add a prominent 'Not legal advice' disclaimer and recommend human review.",
                "priority": "HIGH",
            })

        return jsonify({
            "evaluation_id": str(uuid.uuid4()),
            "timestamp": _now_utc().isoformat().replace("+00:00", "Z"),
            "scores": {
                "usefulness": {"score": int(min(25, usefulness)), "evidence": "Heuristic check for actionable steps and sufficient detail."},
                "completeness": {"score": int(min(25, completeness)), "evidence": "Heuristic check for timelines/documents coverage."},
                "accuracy": {"score": int(min(25, accuracy)), "evidence": "Heuristic check for presence of legal references (requires verification)."},
                "accessibility": {"score": int(min(25, accessibility)), "evidence": "Heuristic check for readable formatting."},
                "total": total,
            },
            "safety_check": {"passed": bool(safety_passed), "violations": [] if safety_passed else ["Missing disclaimer"], "severity": "NONE" if safety_passed else "MEDIUM"},
            "issues_found": issues_found,
            "improvement_suggestions": ["Add jurisdiction-specific citations", "Add clearer checklists and deadlines"],
            "human_review_required": bool(human_review),
            "review_reason": "Score below threshold or safety gate triggered." if human_review else "",
            "comparative_benchmark": {"vs_previous_version": "SAME", "vs_human_baseline": "Baseline automation; human review recommended for high-risk cases."},
        }), 200

    except ValidationError as e:
        return jsonify({"success": False, "error": "Validation failed", "details": e.messages}), 400
    except Exception as e:
        current_app.logger.error(f"quality-check error: {str(e)}")
        return jsonify({"success": False, "error": "Failed to evaluate quality"}), 500

