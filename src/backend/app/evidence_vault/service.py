"""Validate, quarantine, scan, checksum, and promote uploaded evidence."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import os
import secrets
import tempfile

from app.evidence_vault.scanning import MalwareDetected, ScannerUnavailable
from app.evidence_vault.storage import EvidenceStoreError


class InvalidEvidence(ValueError):
    """The uploaded evidence type or file signature is not permitted."""


class EvidenceTooLarge(ValueError):
    """The uploaded evidence exceeded its configured size limit."""


@dataclass(frozen=True)
class EvidenceUploadResult:
    object_key: str
    status: str
    content_type: str
    size_bytes: int
    checksum_sha256: str
    scanner_version: str


_TYPES = {
    ".pdf": ("application/pdf", lambda header: b"%PDF-" in header[:1024]),
    ".png": ("image/png", lambda header: header.startswith(b"\x89PNG\r\n\x1a\n")),
    ".jpg": ("image/jpeg", lambda header: header.startswith(b"\xff\xd8\xff")),
    ".jpeg": ("image/jpeg", lambda header: header.startswith(b"\xff\xd8\xff")),
}


class EvidenceVault:
    def __init__(self, store, scanner, *, max_bytes: int = 15 * 1024 * 1024):
        if max_bytes <= 0:
            raise ValueError("Evidence size limit must be positive.")
        self.store = store
        self.scanner = scanner
        self.max_bytes = max_bytes

    @staticmethod
    def _validate_header(filename: str, content_type: str, header: bytes) -> str:
        suffix = os.path.splitext(filename.lower())[1]
        expected = _TYPES.get(suffix)
        if expected is None or content_type.lower().split(";", 1)[0].strip() != expected[0]:
            raise InvalidEvidence("Evidence must be a supported PDF, PNG, or JPEG file.")
        if not expected[1](header):
            raise InvalidEvidence("Evidence file signature does not match its declared type.")
        return expected[0]

    def upload(self, source, *, filename: str, content_type: str) -> EvidenceUploadResult:
        if not isinstance(filename, str) or len(filename) > 255 or not filename.strip():
            raise InvalidEvidence("Evidence filename is invalid.")
        if not isinstance(content_type, str):
            raise InvalidEvidence("Evidence content type is invalid.")

        descriptor, temporary_path = tempfile.mkstemp(prefix="scmirn-evidence-")
        object_key = secrets.token_hex(32)
        size = 0
        digest = hashlib.sha256()
        prefix = bytearray()
        quarantined = False
        try:
            with os.fdopen(descriptor, "wb") as destination:
                while True:
                    chunk = source.read(min(64 * 1024, self.max_bytes + 1 - size))
                    if not chunk:
                        break
                    size += len(chunk)
                    if size > self.max_bytes:
                        raise EvidenceTooLarge("Evidence exceeds the configured size limit.")
                    digest.update(chunk)
                    if len(prefix) < 1024:
                        prefix.extend(chunk[:1024 - len(prefix)])
                    destination.write(chunk)
                destination.flush()
                os.fsync(destination.fileno())

            normalized_type = self._validate_header(filename, content_type, bytes(prefix))
            self.store.put_quarantine(object_key, temporary_path)
            quarantined = True
            scanner_version = self.scanner.scan(temporary_path)
            if not isinstance(scanner_version, str) or not scanner_version.strip():
                raise ScannerUnavailable("Malware scanner did not provide a verified version.")
            self.store.promote(object_key)
            quarantined = False
            return EvidenceUploadResult(
                object_key=object_key,
                status="CLEAN",
                content_type=normalized_type,
                size_bytes=size,
                checksum_sha256=digest.hexdigest(),
                scanner_version=scanner_version,
            )
        except (ScannerUnavailable, MalwareDetected):
            if quarantined:
                try:
                    self.store.delete(object_key)
                except Exception:
                    raise EvidenceStoreError("Rejected or unscanned evidence cleanup failed.") from None
            raise
        except Exception:
            if quarantined:
                try:
                    self.store.delete(object_key)
                except Exception:
                    raise EvidenceStoreError("Evidence quarantine cleanup failed.") from None
            raise
        finally:
            try:
                os.unlink(temporary_path)
            except FileNotFoundError:
                pass


__all__ = [
    "EvidenceTooLarge", "EvidenceUploadResult", "EvidenceVault", "InvalidEvidence",
]
