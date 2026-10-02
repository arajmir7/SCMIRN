from __future__ import annotations

from app import create_app
from app.extensions import db
from app.infrastructure.database.models import DocumentORM, OfficeORM


def _client():
    app = create_app("testing")
    with app.app_context():
        db.create_all()
    return app, app.test_client()


def test_api_health_route_is_registered():
    app, client = _client()
    try:
        response = client.get("/api/health")
        assert response.status_code == 200
        assert response.get_json() == {"status": "healthy"}
    finally:
        with app.app_context():
            db.session.remove()
            db.drop_all()


def test_office_api_returns_typed_office_records():
    app, client = _client()
    try:
        with app.app_context():
            db.session.add(OfficeORM(
                name="District Service Center",
                department="Public Services",
                address="12 Civic Road",
                lat=28.6,
                lon=77.2,
                phone="011-555-0100",
                timings="Mon-Fri 9:00-17:00",
                services="Certificates, applications",
                rating=4.5,
            ))
            db.session.commit()

        response = client.get("/api/offices")
        assert response.status_code == 200
        payload = response.get_json()
        assert payload["success"] is True
        assert payload["offices"] == [
            {
                "id": 1,
                "name": "District Service Center",
                "department": "Public Services",
                "address": "12 Civic Road",
                "lat": 28.6,
                "lon": 77.2,
                "officer_name": None,
                "phone": "011-555-0100",
                "timings": "Mon-Fri 9:00-17:00",
                "services": "Certificates, applications",
                "rating": 4.5,
            }
        ]
    finally:
        with app.app_context():
            db.session.remove()
            db.drop_all()


def test_document_lookup_returns_metadata_and_json_not_found():
    app, client = _client()
    try:
        with app.app_context():
            db.session.add(DocumentORM(
                public_id="doc123",
                doc_type="rti",
                status="draft",
                title="Water records request",
                file_size=512,
            ))
            db.session.commit()

        response = client.get("/api/documents/doc123")
        assert response.status_code == 200
        assert response.get_json()["data"]["title"] == "Water records request"
        assert client.get("/api/documents/missing").status_code == 404
    finally:
        with app.app_context():
            db.session.remove()
            db.drop_all()


def test_flask_root_no_longer_serves_a_jinja_frontend():
    app, client = _client()
    try:
        response = client.get("/")
        assert response.status_code == 404
        assert response.is_json
    finally:
        with app.app_context():
            db.session.remove()
            db.drop_all()
