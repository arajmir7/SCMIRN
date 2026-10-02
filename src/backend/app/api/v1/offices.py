"""Read-only API for the government office locator."""

from flask import Blueprint, current_app, jsonify

from app.extensions import limiter
from app.infrastructure.database.models import OfficeORM

bp = Blueprint("api_offices", __name__)


@bp.route("/offices", methods=["GET"])
@limiter.limit("100 per minute")
def list_offices():
    try:
        offices = OfficeORM.query.order_by(OfficeORM.rating.desc(), OfficeORM.name.asc()).all()
        return jsonify({
            "success": True,
            "offices": [
                {
                    "id": office.id,
                    "name": office.name,
                    "department": office.department,
                    "address": office.address,
                    "lat": office.lat,
                    "lon": office.lon,
                    "officer_name": office.officer_name,
                    "phone": office.phone,
                    "timings": office.timings,
                    "services": office.services,
                    "rating": office.rating,
                }
                for office in offices
            ],
        }), 200
    except Exception:
        current_app.logger.exception("Unable to load government offices")
        return jsonify({"success": False, "error": "Unable to load government offices"}), 500
