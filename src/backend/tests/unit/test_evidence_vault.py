from __future__ import annotations

from hashlib import sha256
from io import BytesIO
from pathlib import Path
import stat

import pytest

from app.evidence_vault.scanning import ClamAVScanner, MalwareDetected, ScannerUnavailable
from app.evidence_vault.service import EvidenceTooLarge, EvidenceVault, InvalidEvidence
from app.evidence_vault.storage import LocalPrivateStore, S3PrivateStore
from app import create_app
from app.evidence_vault import providers


PDF = b"%PDF-1.7\nprivate claim evidence\n%%EOF"


def test_local_store_provider_rejects_public_roots(monkeypatch):
    app = create_app("testing")
    app.static_folder = str(Path(app.root_path) / "static")
    constructed = []
    monkeypatch.setattr(providers, "LocalPrivateStore", lambda root: constructed.append(root))

    with app.app_context():
        app.config.update(
            EVIDENCE_STORAGE_BACKEND="local",
            SCMIRN_ENVIRONMENT="development",
        )
        for public_root in (app.static_folder, app.config["UPLOAD_FOLDER"]):
            app.config["EVIDENCE_LOCAL_ROOT"] = str(Path(public_root) / "evidence-test")
            with pytest.raises(RuntimeError, match="public or upload"):
                providers.evidence_store()

    assert constructed == []


class CleanScanner:
    def __init__(self):
        self.calls = 0

    def scan(self, path: str) -> str:
        self.calls += 1
        assert Path(path).read_bytes() == PDF
        return "clamav-test/1"


class DownScanner:
    def scan(self, path: str) -> str:
        raise ScannerUnavailable("scanner unavailable")


class InfectedScanner:
    def scan(self, path: str) -> str:
        raise MalwareDetected("malware detected")


def test_clean_pdf_is_scanned_checksummed_and_promoted_to_private_storage(tmp_path):
    store = LocalPrivateStore(tmp_path / "private")
    scanner = CleanScanner()
    result = EvidenceVault(store, scanner, max_bytes=1024).upload(
        BytesIO(PDF), filename="claim.pdf", content_type="application/pdf"
    )

    assert result.status == "CLEAN"
    assert result.checksum_sha256 == sha256(PDF).hexdigest()
    assert result.scanner_version == "clamav-test/1"
    assert scanner.calls == 1
    assert store.object_path(result.object_key).read_bytes() == PDF
    assert stat.S_IMODE(store.object_path(result.object_key).stat().st_mode) == 0o600
    assert stat.S_IMODE(store.root.stat().st_mode) == 0o700
    assert not store.quarantine_path(result.object_key).exists()


def test_mismatched_mime_and_signature_never_reaches_scanner_or_storage(tmp_path):
    store = LocalPrivateStore(tmp_path / "private")
    scanner = CleanScanner()

    with pytest.raises(InvalidEvidence):
        EvidenceVault(store, scanner, max_bytes=1024).upload(
            BytesIO(b"<html>not a PDF</html>"),
            filename="claim.pdf",
            content_type="application/pdf",
        )

    assert scanner.calls == 0
    assert not [path for path in (tmp_path / "private").rglob("*") if path.is_file()]


def test_oversize_upload_is_rejected_before_scanning(tmp_path):
    store = LocalPrivateStore(tmp_path / "private")
    scanner = CleanScanner()

    with pytest.raises(EvidenceTooLarge):
        EvidenceVault(store, scanner, max_bytes=8).upload(
            BytesIO(PDF), filename="claim.pdf", content_type="application/pdf"
        )

    assert scanner.calls == 0
    assert not [path for path in (tmp_path / "private").rglob("*") if path.is_file()]


@pytest.mark.parametrize("scanner", [DownScanner(), InfectedScanner()])
def test_unavailable_or_malicious_scan_never_promotes_evidence(tmp_path, scanner):
    store = LocalPrivateStore(tmp_path / "private")
    error = ScannerUnavailable if isinstance(scanner, DownScanner) else MalwareDetected

    with pytest.raises(error):
        EvidenceVault(store, scanner, max_bytes=1024).upload(
            BytesIO(PDF), filename="claim.pdf", content_type="application/pdf"
        )

    for subdirectory in ("objects", "quarantine"):
        directory = tmp_path / "private" / subdirectory
        assert not [path for path in directory.glob("*") if path.is_file()]


class FakeSocket:
    def __init__(self, response):
        self.response = response
        self.sent = bytearray()

    def settimeout(self, timeout):
        self.timeout = timeout

    def connect(self, address):
        self.address = address

    def sendall(self, value):
        self.sent.extend(value)

    def recv(self, length):
        value, self.response = self.response, b""
        return value

    def close(self):
        pass


def test_clamav_scanner_checks_version_and_stream_result(monkeypatch, tmp_path):
    responses = [FakeSocket(b"ClamAV 1.4.0\0"), FakeSocket(b"stream: OK\0")]
    monkeypatch.setattr("app.evidence_vault.scanning.socket.create_connection", lambda *args, **kwargs: responses.pop(0))
    source = tmp_path / "scan.pdf"
    source.write_bytes(PDF)

    assert ClamAVScanner(host="scanner.internal").scan(str(source)) == "ClamAV 1.4.0"
    assert not responses


def test_clamav_malware_finding_is_never_clean(monkeypatch, tmp_path):
    responses = [FakeSocket(b"ClamAV 1.4.0\0"), FakeSocket(b"stream: Eicar-Test-Signature FOUND\0")]
    monkeypatch.setattr("app.evidence_vault.scanning.socket.create_connection", lambda *args, **kwargs: responses.pop(0))
    source = tmp_path / "scan.pdf"
    source.write_bytes(PDF)

    with pytest.raises(MalwareDetected):
        ClamAVScanner(host="scanner.internal").scan(str(source))


def test_s3_store_uses_private_kms_storage_and_caps_signed_url_ttl(tmp_path):
    class S3Client:
        def __init__(self):
            self.calls = []

        def upload_file(self, *args, **kwargs):
            self.calls.append(("upload", args, kwargs))

        def copy_object(self, **kwargs):
            self.calls.append(("copy", kwargs))

        def delete_object(self, **kwargs):
            self.calls.append(("delete", kwargs))

    source = tmp_path / "source.pdf"
    source.write_bytes(PDF)
    client = S3Client()
    store = S3PrivateStore(bucket="evidence-private", region="ap-south-1", kms_key_id="kms-key", client=client)
    key = "a" * 64

    store.put_quarantine(key, str(source))
    store.promote(key)
    upload = client.calls[0]
    assert upload[1][2] == f"quarantine/{key}"
    assert upload[2]["ExtraArgs"]["ServerSideEncryption"] == "aws:kms"
    assert upload[2]["ExtraArgs"]["SSEKMSKeyId"] == "kms-key"
    assert "ACL" not in upload[2]["ExtraArgs"]
    assert client.calls[1][1]["Key"] == f"evidence/{key}"
    assert len(client.calls) == 3


def test_s3_delete_removes_and_verifies_all_object_versions():
    class VersionedS3Client:
        def __init__(self):
            self.remaining = {
                f"evidence/{'b' * 64}": [{"Key": f"evidence/{'b' * 64}", "VersionId": "v1"}],
                f"quarantine/{'b' * 64}": [],
            }
            self.delete_calls = []

        def delete_object(self, **kwargs):
            self.delete_calls.append(kwargs)
            if kwargs.get("VersionId"):
                self.remaining[kwargs["Key"]] = []

        def list_object_versions(self, *, Bucket, Prefix, **kwargs):
            del Bucket, kwargs
            versions = self.remaining.get(Prefix, [])
            return {"Versions": list(versions), "DeleteMarkers": []}

    client = VersionedS3Client()
    store = S3PrivateStore(bucket="evidence-private", region="ap-south-1", kms_key_id="kms-key", client=client)

    assert store.delete("b" * 64) is True
    assert {call.get("VersionId") for call in client.delete_calls if "VersionId" in call} == {"v1"}
