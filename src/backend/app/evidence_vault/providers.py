"""Resolve private evidence dependencies from explicit deployment configuration."""
from __future__ import annotations

from pathlib import Path

from flask import current_app

from app.evidence_vault.scanning import ClamAVScanner, ScannerUnavailable
from app.evidence_vault.storage import LocalPrivateStore, S3PrivateStore


class UnconfiguredMalwareScanner:
    def scan(self, path: str) -> str:
        del path
        raise ScannerUnavailable("Malware scanner is not configured.")


def _validate_local_root(app) -> Path:
    local_root = Path(app.config["EVIDENCE_LOCAL_ROOT"]).expanduser().resolve()
    public_roots = (app.static_folder, app.config.get("UPLOAD_FOLDER"))
    for configured_root in public_roots:
        if not configured_root:
            continue
        public_root = Path(configured_root).expanduser().resolve()
        try:
            local_root.relative_to(public_root)
        except ValueError:
            continue
        raise RuntimeError("Evidence storage cannot be inside a public or upload directory.")
    return local_root


def evidence_store():
    app = current_app._get_current_object()
    if "scmirn_evidence_store" in app.extensions:
        return app.extensions["scmirn_evidence_store"]
    backend = app.config.get("EVIDENCE_STORAGE_BACKEND", "local")
    if backend == "local" and app.config.get("SCMIRN_ENVIRONMENT") != "production":
        store = LocalPrivateStore(_validate_local_root(app))
    elif backend == "s3":
        store = S3PrivateStore(
            bucket=app.config.get("EVIDENCE_S3_BUCKET", ""),
            region=app.config.get("EVIDENCE_S3_REGION", ""),
            endpoint_url=app.config.get("EVIDENCE_S3_ENDPOINT_URL") or None,
            kms_key_id=app.config.get("EVIDENCE_S3_KMS_KEY_ID", ""),
        )
    else:
        raise RuntimeError("Evidence storage backend is not allowed for this environment.")
    app.extensions["scmirn_evidence_store"] = store
    return store


def malware_scanner():
    app = current_app._get_current_object()
    if "scmirn_evidence_scanner" in app.extensions:
        return app.extensions["scmirn_evidence_scanner"]
    unix_socket = app.config.get("EVIDENCE_CLAMAV_UNIX_SOCKET") or None
    host = app.config.get("EVIDENCE_CLAMAV_HOST") or None
    if not unix_socket and not host:
        scanner = UnconfiguredMalwareScanner()
    else:
        scanner = ClamAVScanner(
            unix_socket=unix_socket,
            host=host,
            port=app.config.get("EVIDENCE_CLAMAV_PORT", 3310),
            timeout=app.config.get("EVIDENCE_CLAMAV_TIMEOUT_SECONDS", 5),
        )
    app.extensions["scmirn_evidence_scanner"] = scanner
    return scanner
