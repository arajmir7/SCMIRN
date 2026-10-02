"""
Blockchain Transparency Layer (v1).

Implements:
 - POST /api/v1/blockchain/register-issue

This is an in-memory demonstration only. It does not connect to a chain or persist records.
"""

from __future__ import annotations

from datetime import datetime, timezone

from flask import Blueprint, jsonify, request, current_app
from marshmallow import Schema, fields, validate, ValidationError

from app.extensions import limiter
from app.utils.crypto import sha256_of_json


bp = Blueprint("api_v1_blockchain", __name__, url_prefix="/api/v1/blockchain")


class LocationSchema(Schema):
    lat = fields.Float(required=True)
    lng = fields.Float(required=True)
    ward = fields.Str(load_default="")


class IssueDataSchema(Schema):
    issue_id = fields.Str(required=True)
    reporter_id = fields.Str(required=True)
    category = fields.Str(required=True)
    description_hash = fields.Str(required=True, validate=validate.Length(min=32, max=128))
    location = fields.Nested(LocationSchema(), required=True)
    media_hashes = fields.List(fields.Str(), load_default=list)
    timestamp = fields.Str(required=True)
    priority = fields.Str(required=True)


class RegisterIssueSchema(Schema):
    issue_data = fields.Nested(IssueDataSchema(), required=True)
    contract_address = fields.Str(load_default="0x0000000000000000000000000000000000000000")


@bp.route("/register-issue", methods=["POST"])
@limiter.limit("60 per minute")
def register_issue():
    """
    POST /api/v1/blockchain/register-issue

    Hashes a synthetic payload in memory. No chain, transaction, or database write exists.
    """
    try:
        schema = RegisterIssueSchema()
        data = schema.load(request.get_json() or {})

        issue_data = data["issue_data"]
        payload_hash = sha256_of_json(issue_data)

        return jsonify({
            "success": True,
            "tx": {
                "tx_hash": None,
                "block_number": None,
                "contract_address": None,
                "status": "SIMULATED",
                "evaluated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            },
            "audit": {
                "payload_hash": payload_hash,
                "verification_note": "Synthetic payload hashed in memory only; nothing was submitted to a blockchain or stored.",
            }
        }), 200

    except ValidationError as e:
        return jsonify({"success": False, "error": "Validation failed", "details": e.messages}), 400
    except Exception as e:
        current_app.logger.error(f"Blockchain register issue error: {str(e)}")
        return jsonify({"success": False, "error": "Failed to register issue on audit ledger"}), 500

