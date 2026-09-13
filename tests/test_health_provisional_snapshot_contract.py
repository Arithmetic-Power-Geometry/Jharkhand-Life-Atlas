from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'modules' / 'health_access' / 'capture_provisional_ogd_snapshot.py'
WORKFLOW = ROOT / '.github' / 'workflows' / 'health-provisional-ogd-snapshot.yml'


def test_snapshot_script_preserves_fail_closed_contract() -> None:
    text = SCRIPT.read_text(encoding='utf-8')
    required = [
        'JLA_PROVISIONAL_OGD_SNAPSHOT_V1',
        'raw_snapshot_persisted',
        'schema_inspected',
        'canonical_source_identity_resolved',
        'publication_allowed',
        'curated_dataset_emitted',
        'snapshot_is_candidate_level_evidence_not_canonical_source_selection',
        'no_geographic_equivalence_may_be_inferred_from_names_alone',
        'missing_values_must_remain_missing_and_must_never_be_silently_zero_filled',
    ]
    missing = [x for x in required if x not in text]
    assert not missing, f'provisional Health snapshot contract lost guards: {missing}'


def test_workflow_archives_exact_bytes_with_receipt_but_never_publishes() -> None:
    text = WORKFLOW.read_text(encoding='utf-8')
    required = [
        'hospital_directory.csv',
        'receipt.json',
        "publication_allowed'] is False",
        "canonical_source_identity_resolved'] is False",
        "curated_dataset_emitted'] is False",
        'retention-days: 90',
    ]
    missing = [x for x in required if x not in text]
    assert not missing, f'provisional snapshot workflow lost guards: {missing}'
