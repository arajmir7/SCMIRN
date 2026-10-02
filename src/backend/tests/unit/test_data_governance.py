from scripts.check_data_governance import (
    load_registry, load_schema, refresh_registry, validate_registry,
)


def _profile():
    return {
        "processing_justification": "REVIEW_REQUIRED",
        "consent_notice_requirement": "REVIEW_REQUIRED",
        "processor": "UNCONFIGURED",
        "storage": "UNVERIFIED",
        "region": "UNCONFIGURED",
        "encryption": "DEPLOYMENT_REVIEW_REQUIRED",
        "authorized_roles": ["NOT_APPROVED"],
        "retention": "UNCONFIGURED",
        "deletion": "NOT_IMPLEMENTED",
        "export": "NOT_IMPLEMENTED",
        "correction": "NOT_IMPLEMENTED",
        "grievance_path": "UNCONFIGURED",
    }


def _registry(columns=("id", "email")):
    return {
        "version": 1,
        "tables": {
            "members": {
                "columns": list(columns),
                "data_boundary_classification": "TEST_SUBJECT_DATA",
                "owner": "test schema owner",
                "scope": "subject",
                "sensitivity": "test personal data",
                "retention_class": "test-only",
            }
        },
        "profiles": {"unreviewed": _profile()},
        "personal_fields": {
            "members.email": {
            "classification": "DIRECT_IDENTIFIER",
            "purpose": "UNASSESSED",
            "profile": "unreviewed",
            "status": "INVENTORIED",
            }
        },
        "nonpersonal_fields": {
            "members.id": {
                "classification": "UNASSESSED",
                "reason": "Synthetic primary key for the fixture.",
                "status": "REVIEWED",
            }
        },
        "candidate_exemptions": {},
    }


def test_persisted_schema_changes_fail_until_inventory_and_personal_record_are_added():
    issues = validate_registry({"members": {"id", "email", "phone"}}, _registry())
    assert any("column inventory differs" in issue for issue in issues)
    assert any("members.phone" in issue and "personal-data record" in issue for issue in issues)


def test_every_new_column_requires_a_record_even_without_a_personal_name():
    issues = validate_registry({"members": {"id", "email", "x7"}}, _registry())
    assert any("Mapped field lacks a data-governance record: members.x7" in issue for issue in issues)


def test_personal_fields_require_complete_governance_metadata():
    registry = _registry()
    del registry["profiles"]["unreviewed"]["region"]
    issues = validate_registry({"members": {"id", "email"}}, registry)
    assert any("region" in issue and "profile" in issue for issue in issues)


def test_release_policy_requires_accountable_approval_for_personal_data():
    issues = validate_registry(
        {"members": {"id", "email"}}, _registry(), require_approved=True
    )
    assert any("has not received accountable approval" in issue for issue in issues)


def test_release_policy_requires_classification_of_all_fields():
    registry = _registry()
    registry["nonpersonal_fields"]["members.id"]["status"] = "UNREVIEWED"
    issues = validate_registry({"members": {"id", "email"}}, registry, require_approved=True)
    assert any("needs explicit classification" in issue for issue in issues)


def test_new_unreviewed_field_cannot_pass_ci_even_after_inventory_is_refreshed():
    registry = refresh_registry({"members": {"id", "email", "phone"}}, _registry())
    issues = validate_registry({"members": {"id", "email", "phone"}}, registry)
    assert any("requires engineering inventory" in issue for issue in issues)


def test_release_approval_checks_unresolved_table_and_processor_controls():
    registry = _registry()
    registry["personal_fields"]["members.email"]["status"] = "APPROVED"
    issues = validate_registry({"members": {"id", "email"}}, registry, require_approved=True)
    assert any("unresolved controls" in issue for issue in issues)


def test_checked_in_registry_covers_every_mapped_column():
    registry = load_registry()
    schema = load_schema()
    issues = validate_registry(schema, registry)
    assert issues == []
