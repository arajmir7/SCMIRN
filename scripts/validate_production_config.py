#!/usr/bin/env python3
"""Fail-closed validation for the production Compose environment file."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlsplit


PLACEHOLDER_MARKERS = ("replace", "example", "changeme", "url_encoded_password")


def parse_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line_number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        match = re.fullmatch(r"([A-Za-z_][A-Za-z0-9_]*)=([^\s#]+)", line)
        if not match:
            raise ValueError(f"line {line_number} must use unquoted KEY=VALUE without spaces")
        name, value = match.groups()
        if name in values:
            raise ValueError(f"duplicate setting: {name}")
        values[name] = value
    return values


def _is_placeholder(value: str) -> bool:
    lowered = value.lower()
    return any(marker in lowered for marker in PLACEHOLDER_MARKERS)


def validate(values: dict[str, str]) -> list[str]:
    errors: list[str] = []

    release_id = values.get("SCMIRN_RELEASE_ID", "")
    if (
        not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,63}", release_id)
        or _is_placeholder(release_id)
        or release_id.lower() in {"latest", "current"}
    ):
        errors.append("SCMIRN_RELEASE_ID must be an immutable, non-placeholder build identifier")

    secrets = []
    for name in ("SCMIRN_SECRET_KEY", "SCMIRN_JWT_SECRET_KEY"):
        value = values.get(name, "")
        if len(value) < 32 or _is_placeholder(value):
            errors.append(f"{name} must be a non-placeholder secret of at least 32 characters")
        secrets.append(value)
    if secrets[0] and secrets[1] and secrets[0] == secrets[1]:
        errors.append("SCMIRN_SECRET_KEY and SCMIRN_JWT_SECRET_KEY must be different values")

    database_url = values.get("DATABASE_URL", "")
    try:
        database = urlsplit(database_url)
        db_options = parse_qs(database.query, strict_parsing=True)
        if database.scheme != "postgresql+psycopg":
            errors.append("DATABASE_URL must use postgresql+psycopg://")
        if not database.hostname or not database.username or not database.password:
            errors.append("DATABASE_URL must include a real host and explicit database credentials")
        if database.hostname and (database.hostname.lower().endswith(".example") or "example." in database.hostname.lower()):
            errors.append("DATABASE_URL must not use an example host")
        if db_options.get("sslmode") != ["verify-full"] or db_options.get("sslrootcert") != ["/run/postgres-ca.crt"]:
            errors.append("DATABASE_URL must verify TLS and the PostgreSQL hostname using /run/postgres-ca.crt")
        if _is_placeholder(database_url):
            errors.append("DATABASE_URL must not contain example credentials or placeholders")
    except ValueError:
        errors.append("DATABASE_URL must be a valid PostgreSQL URL with an unambiguous query")

    redis_url = values.get("REDIS_URL", "")
    try:
        redis = urlsplit(redis_url)
        redis_options = parse_qs(redis.query, strict_parsing=True)
        if redis.scheme != "rediss":
            errors.append("REDIS_URL must use rediss://")
        if not redis.hostname or not redis.password:
            errors.append("REDIS_URL must include a real host and explicit Redis credentials")
        if redis.hostname and (redis.hostname.lower().endswith(".example") or "example." in redis.hostname.lower()):
            errors.append("REDIS_URL must not use an example host")
        if redis_options.get("ssl_ca_certs") != ["/run/redis-ca.crt"]:
            errors.append("REDIS_URL must trust /run/redis-ca.crt")
        if redis_options.get("ssl_cert_reqs") != ["required"]:
            errors.append("REDIS_URL must require certificate verification (ssl_cert_reqs=required)")
        if redis_options.get("ssl_check_hostname", [""])[0].lower() not in {"true", "yes", "1"}:
            errors.append("REDIS_URL must enable hostname verification (ssl_check_hostname=true)")
        if _is_placeholder(redis_url):
            errors.append("REDIS_URL must not contain example credentials or placeholders")
    except ValueError:
        errors.append("REDIS_URL must be a valid Redis URL with an unambiguous query")

    for name in ("SCMIRN_POSTGRES_CA_FILE", "SCMIRN_REDIS_CA_FILE"):
        configured_path = values.get(name, "")
        certificate = Path(configured_path)
        if not certificate.is_absolute() or not certificate.is_file():
            errors.append(f"{name} must point to an existing absolute CA certificate file")

    origins = [origin.strip() for origin in values.get("CORS_ORIGINS", "").split(",") if origin.strip()]
    if not origins:
        errors.append("CORS_ORIGINS must contain at least one explicit HTTPS origin")
    for origin in origins:
        parsed_origin = urlsplit(origin)
        host = (parsed_origin.hostname or "").lower()
        if (
            parsed_origin.scheme != "https"
            or not host
            or parsed_origin.username
            or parsed_origin.password
            or parsed_origin.path
            or parsed_origin.query
            or parsed_origin.fragment
            or "*" in host
            or host == "localhost"
            or host.endswith(".example")
            or "example." in host
        ):
            errors.append("CORS_ORIGINS must contain only explicit, non-placeholder HTTPS origins")
            break

    port = values.get("SCMIRN_HTTP_PORT", "8080")
    if not port.isdigit() or not 1 <= int(port) <= 65535:
        errors.append("SCMIRN_HTTP_PORT must be between 1 and 65535")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env-file", type=Path, required=True, help="Production Compose environment file")
    args = parser.parse_args()
    if not args.env_file.is_file():
        print("ERROR: production environment file does not exist", file=sys.stderr)
        return 2
    try:
        errors = validate(parse_env_file(args.env_file))
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"ERROR: invalid production environment file: {exc}", file=sys.stderr)
        return 2
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("Production config policy passed; secret values were not displayed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
