from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "health-nfhs5-acquisition.yml"


def test_nfhs5_blocker_tracks_current_official_access_without_inventing_identity():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "'data_api_advertised': True" in text
    assert "advertised_on_current_official_ogd_surface_but_exact_machine_identity_not_verified" in text
    assert "'exact_data_api_identity_verified': False" in text
    assert "Do not substitute mirrors" in text
    assert "synthesize an API UUID" in text
    assert "infer an endpoint from the page slug" in text


def test_nfhs5_blocker_remains_publication_fail_closed():
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "'raw_payload_acquired': False" in text
    assert "'sha256_available': False" in text
    assert "'observed_schema_available': False" in text
    assert "'publication_allowed': False" in text
    assert "'missing_values_may_be_converted_to_zero': False" in text
    assert "presence of a Data API control as payload acquisition" in text
