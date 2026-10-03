from __future__ import annotations

import hashlib
import json
import sys
from datetime import date
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPOSITORY_ROOT / "scripts"))

import check_release_blockers as release_blockers  # noqa: E402


def _blocker(**changes):
    value = {
        "id": "ENG-001",
        "title": "Example control",
        "category": "SECURITY",
        "severity": "HIGH",
        "type": "ENGINEERING",
        "state": "OPEN",
        "production_blocking": True,
        "owner_role": "SECURITY_ENGINEER",
        "source_requirement": "A scoped source requirement.",
        "affected_component": "A bounded component.",
        "verification_command": "python -m pytest -q",
        "required_evidence": "evidence/control.json",
        "last_verified_commit": None,
        "last_verified_date": None,
        "closure_reason": None,
    }
    value.update(changes)
    return value


def test_open_engineering_control_fails_candidate_mode():
    issues = release_blockers.validate_ledger(
        {"schema_version": 1, "blockers": [_blocker()]},
        root=REPOSITORY_ROOT,
        mode="candidate",
        today=date(2026, 10, 3),
    )
    assert any("blocking engineering/operational work is OPEN" in issue for issue in issues)


def test_external_dependency_does_not_fail_candidate_but_blocks_authorized_mode():
    blocker = _blocker(
        id="EXT-001", type="GOVERNMENT_AUTHORIZATION",
        state="BLOCKED_EXTERNAL_DEPENDENCY",
    )
    ledger = {"schema_version": 1, "blockers": [blocker]}
    assert release_blockers.validate_ledger(
        ledger, root=REPOSITORY_ROOT, mode="candidate", today=date(2026, 10, 3),
    ) == []
    assert any("not closed for authorized deployment" in issue for issue in release_blockers.validate_ledger(
        ledger, root=REPOSITORY_ROOT, mode="authorized", today=date(2026, 10, 3),
    ))


def test_completed_evidence_must_exist_and_match_current_commit(tmp_path, monkeypatch):
    commit = "a" * 40
    monkeypatch.setattr(release_blockers, "_head", lambda root: commit)
    evidence_path = tmp_path / "evidence/control.json"
    evidence_path.parent.mkdir(parents=True)
    evidence_path.write_text(json.dumps({
        "blocker_id": "ENG-001",
        "state": "LOCALLY_VERIFIED",
        "verified_commit": commit,
        "verified_at": "2026-10-03",
    }), encoding="utf-8")
    blocker = _blocker(
        state="LOCALLY_VERIFIED",
        required_evidence="evidence/control.json",
        last_verified_commit=commit,
        last_verified_date="2026-10-03",
        closure_reason="Disposable unit evidence for the example control.",
    )
    assert release_blockers.validate_ledger(
        {"schema_version": 1, "blockers": [blocker]},
        root=tmp_path,
        mode="candidate",
        today=date(2026, 10, 3),
    ) == []

    blocker["last_verified_commit"] = "b" * 40
    issues = release_blockers.validate_ledger(
        {"schema_version": 1, "blockers": [blocker]},
        root=tmp_path,
        mode="candidate",
        today=date(2026, 10, 3),
    )
    assert any("evidence commit" in issue and "is stale" in issue for issue in issues)


def test_external_approval_cannot_be_self_marked_locally_verified():
    blocker = _blocker(
        id="PRIV-001", type="PRIVACY_LEGAL", state="LOCALLY_VERIFIED",
    )
    issues = release_blockers.validate_ledger(
        {"schema_version": 1, "blockers": [blocker]},
        root=REPOSITORY_ROOT,
        mode="candidate",
        today=date(2026, 10, 3),
    )
    assert any("external requirement must be blocked pending dependency" in issue for issue in issues)


def test_engineering_work_cannot_be_marked_as_externally_blocked():
    blocker = _blocker(state="BLOCKED_EXTERNAL_DEPENDENCY")
    issues = release_blockers.validate_ledger(
        {"schema_version": 1, "blockers": [blocker]},
        root=REPOSITORY_ROOT,
        mode="candidate",
        today=date(2026, 10, 3),
    )
    assert any("cannot be hidden as an external dependency" in issue for issue in issues)


def test_release_inventory_cannot_omit_baseline_controls():
    issues = release_blockers.validate_inventory({"blockers": [_blocker()]})
    assert any("Required baseline blocker records are missing" in issue for issue in issues)


def test_external_approval_requires_signed_artifact_and_protected_trust_root(tmp_path, monkeypatch):
    commit = "c" * 40
    monkeypatch.setattr(release_blockers, "_head", lambda root: commit)
    evidence_path = tmp_path / "evidence/external.json"
    artifact_path = tmp_path / "evidence/approval.pdf"
    evidence_path.parent.mkdir(parents=True)
    artifact_path.write_bytes(b"external authority approval")
    evidence_path.write_text(json.dumps({
        "blocker_id": "EXT-001",
        "state": "EXTERNALLY_VERIFIED",
        "verified_commit": commit,
        "verified_at": "2026-10-03",
        "approver_identity": "authority-reviewer",
        "approver_organization": "authority",
        "approval_reference": "APPROVAL-1",
        "artifact_path": "evidence/approval.pdf",
        "artifact_sha256": hashlib.sha256(artifact_path.read_bytes()).hexdigest(),
    }), encoding="utf-8")
    monkeypatch.delenv("SCMIRN_RELEASE_TRUSTED_KEYRING", raising=False)
    monkeypatch.delenv("SCMIRN_RELEASE_TRUSTED_FINGERPRINTS", raising=False)
    blocker = _blocker(
        id="EXT-001", type="GOVERNMENT_AUTHORIZATION",
        state="EXTERNALLY_VERIFIED",
        required_evidence="evidence/external.json",
        last_verified_commit=commit,
        last_verified_date="2026-10-03",
    )
    issues = release_blockers.validate_ledger(
        {"schema_version": 1, "blockers": [blocker]},
        root=tmp_path,
        mode="authorized",
        today=date(2026, 10, 3),
    )
    assert any("protected trusted-keyring" in issue for issue in issues)
