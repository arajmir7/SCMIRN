"""Private object-store implementations for evidence bytes."""
from __future__ import annotations

from pathlib import Path
import os
import re
import shutil
from typing import BinaryIO


_OBJECT_KEY = re.compile(r"^[a-f0-9]{64}$")


class EvidenceStoreError(RuntimeError):
    """An evidence object could not be safely stored or retrieved."""


def _validate_key(key: str) -> str:
    if not isinstance(key, str) or not _OBJECT_KEY.fullmatch(key):
        raise ValueError("Evidence object key is invalid.")
    return key


class LocalPrivateStore:
    """Filesystem-backed development store; its root must be outside web roots."""

    def __init__(self, root: str | Path):
        self.root = Path(root).expanduser().resolve()
        self.quarantine_dir = self.root / "quarantine"
        self.objects_dir = self.root / "objects"
        self.root.mkdir(mode=0o700, parents=True, exist_ok=True)
        self.quarantine_dir.mkdir(mode=0o700, exist_ok=True)
        self.objects_dir.mkdir(mode=0o700, exist_ok=True)
        for directory in (self.root, self.quarantine_dir, self.objects_dir):
            os.chmod(directory, 0o700)

    def quarantine_path(self, key: str) -> Path:
        return self.quarantine_dir / _validate_key(key)

    def object_path(self, key: str) -> Path:
        return self.objects_dir / _validate_key(key)

    def put_quarantine(self, key: str, source_path: str) -> None:
        destination = self.quarantine_path(key)
        descriptor = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        try:
            with os.fdopen(descriptor, "wb") as output, open(source_path, "rb") as source:
                shutil.copyfileobj(source, output, length=64 * 1024)
                output.flush()
                os.fsync(output.fileno())
        except Exception:
            destination.unlink(missing_ok=True)
            raise

    def promote(self, key: str) -> None:
        source = self.quarantine_path(key)
        destination = self.object_path(key)
        if not source.is_file() or destination.exists():
            raise EvidenceStoreError("Evidence quarantine promotion precondition failed.")
        os.replace(source, destination)
        os.chmod(destination, 0o600)

    def open(self, key: str) -> BinaryIO:
        return self.object_path(key).open("rb")

    def delete(self, key: str) -> bool:
        self.object_path(key).unlink(missing_ok=True)
        self.quarantine_path(key).unlink(missing_ok=True)
        return not self.object_path(key).exists() and not self.quarantine_path(key).exists()

class S3PrivateStore:
    """S3-compatible private store using server-side encryption and short URLs."""

    def __init__(self, *, bucket: str, region: str, endpoint_url: str | None = None, kms_key_id: str | None = None, client=None):
        if not bucket or not region:
            raise ValueError("An evidence bucket and region are required.")
        if not kms_key_id:
            raise ValueError("A customer-managed KMS key is required for evidence storage.")
        if client is None:
            import boto3
            client = boto3.client("s3", region_name=region, endpoint_url=endpoint_url)
        self.client = client
        self.bucket = bucket
        self.kms_key_id = kms_key_id

    @staticmethod
    def _quarantine_key(key: str) -> str:
        return f"quarantine/{_validate_key(key)}"

    @staticmethod
    def _object_key(key: str) -> str:
        return f"evidence/{_validate_key(key)}"

    def put_quarantine(self, key: str, source_path: str) -> None:
        self.client.upload_file(
            source_path,
            self.bucket,
            self._quarantine_key(key),
            ExtraArgs={
                "ServerSideEncryption": "aws:kms",
                "SSEKMSKeyId": self.kms_key_id,
                "ContentType": "application/octet-stream",
            },
        )

    def promote(self, key: str) -> None:
        source = self._quarantine_key(key)
        destination = self._object_key(key)
        self.client.copy_object(
            Bucket=self.bucket,
            Key=destination,
            CopySource={"Bucket": self.bucket, "Key": source},
            ServerSideEncryption="aws:kms",
            SSEKMSKeyId=self.kms_key_id,
            ContentType="application/octet-stream",
            MetadataDirective="REPLACE",
        )
        self.client.delete_object(Bucket=self.bucket, Key=source)

    def open(self, key: str) -> BinaryIO:
        return self.client.get_object(Bucket=self.bucket, Key=self._object_key(key))["Body"]

    def delete(self, key: str) -> bool:
        object_key = self._object_key(key)
        quarantine_key = self._quarantine_key(key)
        try:
            for object_name in (object_key, quarantine_key):
                self.client.delete_object(Bucket=self.bucket, Key=object_name)
                for version_id in self._list_version_ids(object_name):
                    self.client.delete_object(
                        Bucket=self.bucket, Key=object_name, VersionId=version_id,
                    )
                if self._list_version_ids(object_name):
                    return False
        except Exception:
            raise EvidenceStoreError("Evidence object deletion could not be verified.") from None
        return True

    def _list_version_ids(self, object_name: str) -> list[str]:
        markers = []
        request = {"Bucket": self.bucket, "Prefix": object_name}
        while True:
            page = self.client.list_object_versions(**request)
            for collection_name in ("Versions", "DeleteMarkers"):
                markers.extend(
                    row["VersionId"]
                    for row in page.get(collection_name, [])
                    if row.get("Key") == object_name and row.get("VersionId") is not None
                )
            if not page.get("IsTruncated"):
                return markers
            key_marker = page.get("NextKeyMarker")
            version_marker = page.get("NextVersionIdMarker")
            if not key_marker or not version_marker:
                raise EvidenceStoreError("Evidence object version listing was incomplete.")
            request["KeyMarker"] = key_marker
            request["VersionIdMarker"] = version_marker
