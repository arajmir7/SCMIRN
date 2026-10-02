"""
Lightweight crypto helpers used across SCMIRN services.

Note: This is NOT a replacement for a real blockchain client. It provides
deterministic hashing for audit trails and tamper-evidence.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any


def canonical_json_dumps(obj: Any) -> str:
    """
    Deterministically serialize JSON-like objects (dict/list/primitives).
    Ensures stable hashes across environments.
    """
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)


def sha256_hex(data: str | bytes) -> str:
    """Return SHA-256 hex digest for input."""
    if isinstance(data, str):
        data = data.encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def sha256_of_json(obj: Any) -> str:
    """Return SHA-256 of canonical JSON representation of obj."""
    return sha256_hex(canonical_json_dumps(obj))

