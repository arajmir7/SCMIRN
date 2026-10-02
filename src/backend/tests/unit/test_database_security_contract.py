from __future__ import annotations

import re
from pathlib import Path

from app.extensions import db
from app.infrastructure.database.security import (
    AUDIT_TABLES_HIDDEN_FROM_APP,
    TENANT_RLS_TABLES,
)
from app.infrastructure.database.models import (  # noqa: F401
    BlockchainTransactionORM,
    ChatLogORM,
    DocumentORM,
    IoTAssetORM,
    IoTReadingORM,
    IssueORM,
    OfficeORM,
    ResilienceHubORM,
    SRSAssetORM,
    SRSAuditLogORM,
    SRSBudgetEventORM,
    SRSContractorORM,
    SRSIssueEventORM,
    SRSIssueORM,
    SRSUtilityMapORM,
    SRSWorkOrderORM,
    UserGamificationORM,
    UserORM,
)
from app.source_routing.audit_models import AuditEvent  # noqa: F401
from app.source_routing.models import (  # noqa: F401
    Authority,
    GovernmentService,
    OfficialSource,
    RouteDecision,
    RouteRule,
    government_service_sources,
)
from app.staff_auth.models import (  # noqa: F401
    StaffAuditEvent,
    StaffCase,
    StaffCaseEvent,
    StaffMfaChallenge,
    StaffMfaFactor,
    StaffRoleGrant,
    StaffSession,
    StaffUser,
    Tenant,
)


REPO_ROOT = Path(__file__).resolve().parents[4]


def test_data_boundary_matrix_covers_every_mapped_table_once():
    matrix = (REPO_ROOT / "docs/security/DATA_BOUNDARY_MATRIX.md").read_text(encoding="utf-8")
    inventory = re.findall(r"^\| `([a-z_]+)` \| `([A-Z_]+)` \|", matrix, re.MULTILINE)
    names = [name for name, _classification in inventory]
    assert len(names) == 34
    assert len(names) == len(set(names))
    assert set(names) == set(db.metadata.tables)
    assert {classification for _name, classification in inventory} <= {
        "GLOBAL_REFERENCE", "TENANT_SCOPED", "SUBJECT_SCOPED",
        "SECURITY_SCOPED", "AUDIT_SCOPED", "LEGACY_UNCLASSIFIED",
    }


def test_runtime_rls_and_audit_hidden_table_contract_is_explicit():
    assert set(TENANT_RLS_TABLES) == {
        "tenants", "staff_users", "staff_mfa_factors", "staff_mfa_challenges",
        "staff_role_grants", "staff_sessions", "staff_cases",
        "staff_case_events", "staff_audit_events",
    }
    assert set(AUDIT_TABLES_HIDDEN_FROM_APP) == {
        "audit_events", "staff_audit_events", "srs_audit_logs",
    }
