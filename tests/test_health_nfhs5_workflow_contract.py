from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "health-nfhs5-acquisition.yml"


def test_nfhs5_blocker_tracks_current_official_access_without_inventing_identity():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "'indexed_metadata_xls_advertised': True" in text
    assert "'indexed_metadata_data_api_control_advertised': True" in text
    assert "'live_catalog_api_control_visible': True" in text
    assert "'catalog_api_identity_scope': 'catalog_only_not_resource_or_payload'" in text
    assert "'exact_payload_identity_verified_from_live_surface': False" in text
    assert "Do not treat indexed metadata, catalog/API/ZIP controls" in text
    assert "do not substitute mirrors or synthesize an endpoint" in text


def test_nfhs5_blocker_remains_publication_fail_closed():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "'raw_payload_acquired': False" in text
    assert "'sha256_available': False" in text
    assert "'observed_schema_available': False" in text
    assert "'publication_allowed': False" in text
    assert "'missing_values_may_be_converted_to_zero': False" in text
    assert "catalog_api_identity_scope" in text
    assert "catalog_only_not_resource_or_payload" in text
