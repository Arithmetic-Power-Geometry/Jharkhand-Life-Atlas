from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'modules' / 'health_access' / 'capture_provisional_ogd_snapshot.py'
WORKFLOW = ROOT / '.github' / 'workflows' / 'health-provisional-ogd-snapshot.yml'


def test_snapshot_script_preserves_fail_closed_contract() -> None:
    text = SCRIPT.read_text(encoding='utf-8')
    required = [
        'JLA_PROVISIONAL_OGD_SNAPSHOT_V2',
        'raw_snapshot_persisted',
        'ephemeral_ci_workspace_only_not_artifact_export',
        'schema_inspected',
        'row_values_recorded_in_receipt',
        'privacy_header_audit_performed',
        'privacy_risk_columns',
        'privacy_review_required',
        'canonical_source_identity_resolved',
        'publication_allowed',
        'curated_dataset_emitted',
        'raw_candidate_bytes_must_not_be_exported_as_ci_artifacts',
        'receipt_must_not_contain_source_row_values',
        'privacy_risk_columns_require_exclusion_or_explicit_rights_and_safety_review_before_any_public_projection',
        'snapshot_is_candidate_level_evidence_not_canonical_source_selection',
        'no_geographic_equivalence_may_be_inferred_from_names_alone',
        'missing_values_must_remain_missing_and_must_never_be_silently_zero_filled',
    ]
    missing = [x for x in required if x not in text]
    assert not missing, f'provisional Health snapshot contract lost guards: {missing}'


def test_workflow_exports_receipt_only_and_never_raw_candidate() -> None:
    text = WORKFLOW.read_text(encoding='utf-8')
    required = [
        'hospital_directory.csv',
        'receipt.json',
        "privacy_review_required'] is True",
        "row_values_recorded_in_receipt'] is False",
        "publication_allowed'] is False",
        "canonical_source_identity_resolved'] is False",
        "curated_dataset_emitted'] is False",
        'rm -f build/health_provisional_snapshot/hospital_directory.csv',
        'build/health_provisional_snapshot/receipt.json',
        'build/health_provisional_snapshot/run.log',
        'retention-days: 90',
    ]
    missing = [x for x in required if x not in text]
    assert not missing, f'provisional snapshot workflow lost privacy/publication guards: {missing}'
