#!/usr/bin/env python3
"""Fail closed when a source feature lacks one evidenced merge disposition."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "docs" / "merge" / "feature-parity.json"
ALLOWED = {"INTEGRATED", "SUPERSEDED", "EXPLICITLY_REJECTED"}


def main() -> int:
    try:
        document = json.loads(MANIFEST.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"feature parity: cannot read manifest: {exc}", file=sys.stderr)
        return 2

    sources = document.get("source_real_features")
    dispositions = document.get("final_dispositions")
    if not isinstance(sources, list) or not isinstance(dispositions, list):
        print("feature parity: source_real_features and final_dispositions must be arrays", file=sys.stderr)
        return 2

    source_ids = [row.get("id") for row in sources if isinstance(row, dict)]
    rows_by_id: dict[str, list[dict]] = {}
    for row in dispositions:
        if isinstance(row, dict) and isinstance(row.get("id"), str):
            rows_by_id.setdefault(row["id"], []).append(row)

    duplicates = sorted(identifier for identifier, rows in rows_by_id.items() if len(rows) != 1)
    source_set = set(source_ids)
    extra = sorted(set(rows_by_id) - source_set)
    missing: list[str] = []
    invalid: list[str] = []
    for identifier in source_ids:
        rows = rows_by_id.get(identifier, [])
        if len(rows) != 1:
            missing.append(identifier)
            continue
        row = rows[0]
        disposition = row.get("disposition")
        if disposition not in ALLOWED:
            invalid.append(f"{identifier}={disposition!r}")
            continue
        if disposition == "INTEGRATED" and not row.get("evidence"):
            invalid.append(f"{identifier}=INTEGRATED without evidence")
        if disposition == "SUPERSEDED" and not row.get("superseded_by"):
            invalid.append(f"{identifier}=SUPERSEDED without superseded_by")
        if disposition == "EXPLICITLY_REJECTED" and not row.get("reason"):
            invalid.append(f"{identifier}=EXPLICITLY_REJECTED without reason")

    integrated = sum(row.get("disposition") == "INTEGRATED" for rows in rows_by_id.values() for row in rows)
    superseded = sum(row.get("disposition") == "SUPERSEDED" for rows in rows_by_id.values() for row in rows)
    rejected = sum(row.get("disposition") == "EXPLICITLY_REJECTED" for rows in rows_by_id.values() for row in rows)
    unexplained = len(missing) + len(invalid) + len(extra) + len(duplicates)
    print(f"SOURCE_REAL_FEATURES={len(sources)}")
    print(f"INTEGRATED={integrated}")
    print(f"SUPERSEDED={superseded}")
    print(f"EXPLICITLY_REJECTED={rejected}")
    print(f"UNEXPLAINED={unexplained}")
    if missing:
        print("Missing/duplicate disposition:", ", ".join(missing))
    if invalid:
        print("Invalid disposition evidence:", "; ".join(invalid))
    if extra:
        print("Unknown source feature IDs:", ", ".join(extra))
    if duplicates:
        print("Duplicate disposition IDs:", ", ".join(duplicates))
    return 0 if unexplained == 0 and integrated + superseded + rejected == len(sources) else 1


if __name__ == "__main__":
    raise SystemExit(main())
