"""Disposable PostgreSQL verification for forced staff tenant policies.

Set SCMIRN_POSTGRES_RLS_TEST_URL to a local disposable PostgreSQL owner URL.
The test creates and drops one uniquely named temporary database and role.
"""
from __future__ import annotations

import os
import secrets
import tempfile
import uuid
import base64
import hashlib
import hmac
import struct
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from sqlalchemy.exc import DBAPIError

import app as app_package
from app import create_app
from app.config import TestingConfig, config_by_name
from app.extensions import db


def _totp(secret: str) -> str:
    counter = int(time.time() // 30)
    key = base64.b32decode(secret + "=" * (-len(secret) % 8))
    digest_bytes = hmac.new(key, struct.pack(">Q", counter), hashlib.sha1).digest()
    offset = digest_bytes[-1] & 0x0F
    value = (struct.unpack(">I", digest_bytes[offset:offset + 4])[0] & 0x7FFFFFFF) % 1_000_000
    return f"{value:06d}"


_TEST_PASSWORD = f"Test-{secrets.token_urlsafe(18)}-A9!"
_NEW_TEST_PASSWORD = f"Changed-{secrets.token_urlsafe(18)}-B7!"


@pytest.mark.integration
def test_forced_staff_rls_with_non_owner_runtime_role(monkeypatch):
    owner_url_text = os.getenv("SCMIRN_POSTGRES_RLS_TEST_URL")
    if not owner_url_text:
        pytest.skip("SCMIRN_POSTGRES_RLS_TEST_URL is not configured")
    owner_url = make_url(owner_url_text)
    if owner_url.get_backend_name() != "postgresql":
        pytest.fail("SCMIRN_POSTGRES_RLS_TEST_URL must point to PostgreSQL")

    suffix = uuid.uuid4().hex[:12]
    database_name = f"scmirn_rls_{suffix}"
    role_name = f"scmirn_runtime_{suffix}"
    role_password = f"test-only-{uuid.uuid4().hex}"
    root_engine = create_engine(owner_url)
    with root_engine.connect().execution_options(isolation_level="AUTOCOMMIT") as connection:
        connection.execute(text(f'CREATE DATABASE "{database_name}"'))
        connection.execute(text(f"CREATE ROLE {role_name} LOGIN PASSWORD '{role_password}'"))

    test_url = owner_url.set(database=database_name)
    runtime_url = test_url.set(username=role_name, password=role_password)
    runtime_engine = None
    test_admin_engine = create_engine(test_url)
    app = None
    runtime_app = None
    try:
        class PostgresMigrationTestConfig(TestingConfig):
            AUTO_CREATE_DB = False
            AUTO_SEED_ROUTING_REGISTRY = False
            STAFF_AUTH_ENABLED = True
            SQLALCHEMY_DATABASE_URI = test_url.render_as_string(hide_password=False)

        monkeypatch.setitem(config_by_name, "postgres_rls_test", PostgresMigrationTestConfig)
        monkeypatch.setattr(app_package.app_config, "DATA_DIR", tempfile.mkdtemp(prefix="scmirn-pg-rls-data-"))
        monkeypatch.setattr(app_package.config_by_name["postgres_rls_test"], "UPLOAD_FOLDER", tempfile.mkdtemp(prefix="scmirn-pg-rls-uploads-"), raising=False)
        app = create_app("postgres_rls_test")
        migrations = Path(__file__).resolve().parents[2] / "app/infrastructure/database/migrations"
        with app.app_context():
            alembic_config = Config(str(migrations / "alembic.ini"))
            alembic_config.set_main_option("script_location", str(migrations))
            command.upgrade(alembic_config, "head")

        tenant_scoped_tables = (
            "tenants", "staff_users", "staff_mfa_factors", "staff_mfa_challenges",
            "staff_role_grants", "staff_sessions", "staff_cases",
            "staff_case_events", "staff_audit_events",
        )
        staff_tables = (
            "staff_users", "staff_mfa_factors", "staff_mfa_challenges",
            "staff_role_grants", "staff_sessions", "staff_cases",
            "staff_case_events", "staff_audit_events",
        )
        with test_admin_engine.begin() as connection:
            connection.execute(text(f"GRANT CONNECT ON DATABASE {database_name} TO {role_name}"))
            connection.execute(text(f"GRANT USAGE ON SCHEMA public TO {role_name}"))
            connection.execute(text(f"GRANT SELECT, INSERT, UPDATE, DELETE ON tenants TO {role_name}"))
            connection.execute(text(
                f"GRANT SELECT, INSERT, UPDATE, DELETE ON {', '.join(staff_tables)} TO {role_name}"
            ))

        now = datetime.now(timezone.utc)
        tenant_a, tenant_b = str(uuid.uuid4()), str(uuid.uuid4())
        user_a, user_b = str(uuid.uuid4()), str(uuid.uuid4())
        session_hash_a, session_hash_b, session_hash_a2 = "a" * 64, "b" * 64, "e" * 64
        with test_admin_engine.begin() as connection:
            connection.execute(text("INSERT INTO tenants (id, slug, display_name, active, created_at) VALUES (:id, :slug, :name, true, :now)"), [
                {"id": tenant_a, "slug": "tenant-a", "name": "Tenant A", "now": now},
                {"id": tenant_b, "slug": "tenant-b", "name": "Tenant B", "now": now},
            ])
            connection.execute(text("INSERT INTO staff_users (id, tenant_id, email, display_name, password_hash, active, failed_login_count, created_at, password_changed_at) VALUES (:id, :tenant, :email, 'Test User', 'unused-hash', true, 0, :now, :now)"), [
                {"id": user_a, "tenant": tenant_a, "email": "a@example.test", "now": now},
                {"id": user_b, "tenant": tenant_b, "email": "b@example.test", "now": now},
            ])
            connection.execute(text("INSERT INTO staff_sessions (session_hash, tenant_id, user_id, csrf_hash, mfa_verified_at, created_at, last_seen_at, idle_expires_at, absolute_expires_at) VALUES (:hash, :tenant, :user, :csrf, :now, :now, :now, :idle, :absolute)"), [
                {"hash": session_hash_a, "tenant": tenant_a, "user": user_a, "csrf": "c" * 64, "now": now, "idle": now + timedelta(minutes=30), "absolute": now + timedelta(hours=12)},
                {"hash": session_hash_b, "tenant": tenant_b, "user": user_b, "csrf": "d" * 64, "now": now, "idle": now + timedelta(minutes=30), "absolute": now + timedelta(hours=12)},
                {"hash": session_hash_a2, "tenant": tenant_a, "user": user_a, "csrf": "e" * 64, "now": now, "idle": now + timedelta(minutes=30), "absolute": now + timedelta(hours=12)},
            ])

        runtime_engine = create_engine(runtime_url)
        with runtime_engine.connect() as connection:
            role_state = connection.execute(text("SELECT rolsuper, rolbypassrls FROM pg_roles WHERE rolname = current_user")).one()
            assert role_state.rolsuper is False
            assert role_state.rolbypassrls is False
            forced = connection.execute(text("SELECT relname, relrowsecurity, relforcerowsecurity, pg_get_userbyid(relowner) AS owner FROM pg_class WHERE relname = ANY(:tables)"), {"tables": list(tenant_scoped_tables)}).all()
            assert len(forced) == len(tenant_scoped_tables)
            assert all(row.relrowsecurity and row.relforcerowsecurity and row.owner != role_name for row in forced)
            policies = connection.execute(text("SELECT tablename, policyname FROM pg_policies WHERE schemaname = 'public' AND tablename = ANY(:tables)"), {"tables": list(tenant_scoped_tables)}).all()
            assert {row.tablename for row in policies} == set(tenant_scoped_tables)
            assert connection.execute(text("SELECT count(*) FROM staff_users")).scalar_one() == 0
            tenant_directory = connection.execute(text("SELECT count(*) FROM tenants")).scalar_one()
            assert tenant_directory == 2

        with runtime_engine.begin() as connection:
            connection.execute(text("SELECT set_config('scmirn.tenant_id', :tenant, true)"), {"tenant": tenant_a})
            visible_users = connection.execute(text("SELECT id FROM staff_users")).scalars().all()
            assert visible_users == [user_a]
            visible_cases = connection.execute(text("SELECT count(*) FROM staff_cases")).scalar_one()
            assert visible_cases == 0

        with runtime_engine.begin() as connection:
            connection.execute(text("SELECT set_config('scmirn.tenant_id', :tenant, true)"), {"tenant": tenant_a})
            with pytest.raises(DBAPIError):
                with connection.begin_nested():
                    connection.execute(text("INSERT INTO staff_cases (id, tenant_id, case_ref, case_type, title, status, priority, created_by, created_at, updated_at) VALUES (:id, :tenant, 'CROSS', 'WATER', 'Water service case', 'OPEN', 'NORMAL', :user, :now, :now)"), {
                        "id": str(uuid.uuid4()), "tenant": tenant_b, "user": user_b, "now": now,
                    })

        with runtime_engine.begin() as connection:
            connection.execute(text("SELECT set_config('scmirn.staff_session_hash', :token, true)"), {"token": session_hash_a})
            assert connection.execute(text("SELECT session_hash FROM staff_sessions")).scalars().all() == [session_hash_a]

        with runtime_engine.begin() as connection:
            connection.execute(text("SELECT set_config('scmirn.tenant_id', :tenant, true)"), {"tenant": tenant_a})
            connection.execute(text("SELECT set_config('scmirn.staff_manage_user_id', :user, true)"), {"user": user_a})
            managed_hashes = connection.execute(text("SELECT session_hash FROM staff_sessions ORDER BY session_hash")).scalars().all()
            assert managed_hashes == sorted([session_hash_a, session_hash_a2])

        with runtime_engine.begin() as connection:
            connection.execute(text("SELECT set_config('scmirn.tenant_id', :tenant, true)"), {"tenant": tenant_a})
            new_session_hash = "f" * 64
            connection.execute(text("SELECT set_config('scmirn.staff_session_hash', :token, true)"), {"token": new_session_hash})
            connection.execute(text("INSERT INTO staff_sessions (session_hash, tenant_id, user_id, csrf_hash, mfa_verified_at, created_at, last_seen_at, idle_expires_at, absolute_expires_at) VALUES (:hash, :tenant, :user, :csrf, :now, :now, :now, :idle, :absolute)"), {
                "hash": new_session_hash, "tenant": tenant_a, "user": user_a,
                "csrf": "f" * 64, "now": now, "idle": now + timedelta(minutes=30),
                "absolute": now + timedelta(hours=12),
            })

        # Cross-tenant user references fail even when the case row itself is in scope.
        with runtime_engine.begin() as connection:
            connection.execute(text("SELECT set_config('scmirn.tenant_id', :tenant, true)"), {"tenant": tenant_a})
            with pytest.raises(DBAPIError):
                with connection.begin_nested():
                    connection.execute(text("INSERT INTO staff_cases (id, tenant_id, case_ref, case_type, title, status, priority, created_by, created_at, updated_at) VALUES (:id, :tenant, 'BADREF', 'WATER', 'Water service case', 'OPEN', 'NORMAL', :user, :now, :now)"), {
                        "id": str(uuid.uuid4()), "tenant": tenant_a, "user": user_b, "now": now,
                    })

        secret = "JBSWY3DPEHPK3PXP"
        class PostgresRuntimeTestConfig(TestingConfig):
            AUTO_CREATE_DB = False
            AUTO_SEED_ROUTING_REGISTRY = False
            STAFF_AUTH_ENABLED = True
            SQLALCHEMY_DATABASE_URI = runtime_url.render_as_string(hide_password=False)

        monkeypatch.setitem(config_by_name, "postgres_runtime_test", PostgresRuntimeTestConfig)
        runtime_app = create_app("postgres_runtime_test")
        with runtime_app.app_context():
            from app.staff_auth.security import encrypt_totp_secret, hash_password
            password_hash = hash_password(_TEST_PASSWORD)
            encrypted_secret = encrypt_totp_secret(secret)
        with test_admin_engine.begin() as connection:
            connection.execute(text("INSERT INTO staff_mfa_factors (id, tenant_id, user_id, secret_ciphertext, active, last_totp_step, failed_attempts, created_at) VALUES (:id, :tenant, :user, :secret, true, -1, 0, :now)"), {
                "id": str(uuid.uuid4()), "tenant": tenant_a, "user": user_a,
                "secret": encrypted_secret, "now": now,
            })
            connection.execute(text("INSERT INTO staff_role_grants (id, tenant_id, user_id, role, created_at) VALUES (:id, :tenant, :user, 'CASE_OFFICER', :now)"), {
                "id": str(uuid.uuid4()), "tenant": tenant_a, "user": user_a, "now": now,
            })
            connection.execute(text("UPDATE staff_users SET password_hash = :hash WHERE id = :user"), {"hash": password_hash, "user": user_a})
            connection.execute(text("INSERT INTO staff_cases (id, tenant_id, case_ref, case_type, title, status, priority, created_by, created_at, updated_at) VALUES (:id, :tenant, 'FOREIGN', 'WATER', 'Water service case', 'OPEN', 'NORMAL', :user, :now, :now)"), {
                "id": str(uuid.uuid4()), "tenant": tenant_b, "user": user_b, "now": now,
            })
            foreign_case_id = connection.execute(text("SELECT id FROM staff_cases WHERE tenant_id = :tenant"), {"tenant": tenant_b}).scalar_one()

        client = runtime_app.test_client()
        challenge_response = client.post("/api/v1/staff/auth/login", json={
            "tenant_slug": "tenant-a", "email": "a@example.test", "password": _TEST_PASSWORD,
        })
        assert challenge_response.status_code == 200
        mfa_response = client.post("/api/v1/staff/auth/mfa", json={
            "challenge": challenge_response.json["challenge"], "code": _totp(secret),
        })
        assert mfa_response.status_code == 200
        assert client.get("/api/v1/staff/auth/me").status_code == 200
        assert client.get(f"/api/v1/staff/cases/{foreign_case_id}").status_code == 404
        csrf_token = client.get_cookie("scmirn_staff_csrf").value
        case_response = client.post("/api/v1/staff/cases", json={"case_type": "WATER"}, headers={"X-CSRF-Token": csrf_token})
        assert case_response.status_code == 201
        case_id = case_response.json["case"]["id"]
        status_response = client.post(
            f"/api/v1/staff/cases/{case_id}/status",
            json={"status": "UNDER_REVIEW"}, headers={"X-CSRF-Token": csrf_token},
        )
        assert status_response.status_code == 200
        with test_admin_engine.connect() as connection:
            case_event_id = connection.execute(text("SELECT id FROM staff_case_events WHERE case_id = :case AND event_type = 'STATUS_CHANGED'"), {"case": case_id}).scalar_one()
            audit_event_id = connection.execute(text("SELECT id FROM staff_audit_events WHERE tenant_id = :tenant AND action = 'CASE_STATUS_CHANGED' ORDER BY created_at DESC LIMIT 1"), {"tenant": tenant_a}).scalar_one()
        with runtime_engine.begin() as connection:
            connection.execute(text("SELECT set_config('scmirn.tenant_id', :tenant, true)"), {"tenant": tenant_a})
            for statement, values in (
                ("UPDATE staff_case_events SET to_status = 'CLOSED' WHERE id = :id", {"id": case_event_id}),
                ("DELETE FROM staff_case_events WHERE id = :id", {"id": case_event_id}),
                ("UPDATE staff_audit_events SET action = 'MODIFIED' WHERE id = :id", {"id": audit_event_id}),
                ("DELETE FROM staff_audit_events WHERE id = :id", {"id": audit_event_id}),
            ):
                with pytest.raises(DBAPIError):
                    with connection.begin_nested():
                        connection.execute(text(statement), values)
        password_response = client.post("/api/v1/staff/auth/password/change", json={
            "current_password": _TEST_PASSWORD, "new_password": _NEW_TEST_PASSWORD,
        }, headers={"X-CSRF-Token": csrf_token})
        assert password_response.status_code == 200
        assert client.get("/api/v1/staff/auth/me").status_code == 401
    finally:
        if runtime_engine is not None:
            runtime_engine.dispose()
        test_admin_engine.dispose()
        if app is not None:
            with app.app_context():
                db.session.remove()
                db.engine.dispose()
        if runtime_app is not None:
            with runtime_app.app_context():
                db.session.remove()
                db.engine.dispose()
        with root_engine.connect().execution_options(isolation_level="AUTOCOMMIT") as connection:
            connection.execute(text(f'DROP DATABASE IF EXISTS "{database_name}" WITH (FORCE)'))
            connection.execute(text(f"DROP ROLE IF EXISTS {role_name}"))
        root_engine.dispose()
