from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[4]
SPEC = importlib.util.spec_from_file_location(
    "validate_production_config",
    REPO_ROOT / "scripts" / "validate_production_config.py",
)
policy = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(policy)


@pytest.fixture
def secure_settings(tmp_path):
    postgres_ca = tmp_path / "postgres-ca.pem"
    redis_ca = tmp_path / "redis-ca.pem"
    postgres_ca.write_text("synthetic CA fixture", encoding="utf-8")
    redis_ca.write_text("synthetic CA fixture", encoding="utf-8")
    return {
        "SCMIRN_RELEASE_ID": "build-20261001-a13f9c2",
        "SCMIRN_SECRET_KEY": "s" * 48,
        "SCMIRN_JWT_SECRET_KEY": "j" * 48,
        "DATABASE_URL": "postgresql+psycopg://dbuser:dbpass@db.internal:5432/scmirn?sslmode=verify-full&sslrootcert=/run/postgres-ca.crt",
        "REDIS_URL": "rediss://:redispass@redis.internal:6380/0?ssl_ca_certs=/run/redis-ca.crt&ssl_cert_reqs=required&ssl_check_hostname=true",
        "SCMIRN_POSTGRES_CA_FILE": str(postgres_ca),
        "SCMIRN_REDIS_CA_FILE": str(redis_ca),
        "CORS_ORIGINS": "https://civic.gov.in",
        "SCMIRN_HTTP_PORT": "8080",
    }


def test_policy_accepts_explicit_secrets_tls_ca_and_https_origins(secure_settings):
    assert policy.validate(secure_settings) == []


def test_policy_rejects_redis_without_hostname_verification(secure_settings):
    secure_settings["REDIS_URL"] = secure_settings["REDIS_URL"].replace(
        "ssl_check_hostname=true", "ssl_check_hostname=false"
    )
    assert any("hostname verification" in error for error in policy.validate(secure_settings))


def test_policy_rejects_duplicate_secrets_and_missing_ca(secure_settings):
    secure_settings["SCMIRN_JWT_SECRET_KEY"] = secure_settings["SCMIRN_SECRET_KEY"]
    secure_settings["SCMIRN_REDIS_CA_FILE"] = "/missing/redis-ca.pem"
    errors = policy.validate(secure_settings)
    assert any("must be different" in error for error in errors)
    assert any("SCMIRN_REDIS_CA_FILE" in error for error in errors)


def test_policy_rejects_placeholder_cors_origin(secure_settings):
    secure_settings["CORS_ORIGINS"] = "https://scmirn.example.gov.in"
    assert any("non-placeholder HTTPS origins" in error for error in policy.validate(secure_settings))


def test_env_parser_rejects_duplicate_keys(tmp_path):
    env_file = tmp_path / "duplicate.env"
    env_file.write_text("SCMIRN_SECRET_KEY=a\nSCMIRN_SECRET_KEY=b\n", encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate setting"):
        policy.parse_env_file(env_file)
