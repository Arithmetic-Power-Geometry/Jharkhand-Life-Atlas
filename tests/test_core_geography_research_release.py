from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "modules" / "core_geography" / "module.yaml"
RELEASE = ROOT / "modules" / "core_geography" / "research_release.yaml"


def _load(path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_research_release_scope_matches_verified_module_metadata():
    module = _load(MODULE)
    release = _load(RELEASE)
    scope = release["verified_release_scope"]
    assert scope["module_status"] == module["status"] == "complete"
    assert scope["module_version"] == module["version"]
    assert scope["census_2011"]["districts"] == 24
    assert scope["census_2011"]["villages"] == 32624
    assert scope["current_lgd"]["villages"] == 32962
    assert scope["dchb_village_amenities"]["verified_rows"] == 32394


def test_research_release_does_not_claim_submission_publication_or_doi():
    release = _load(RELEASE)
    assert release["status"] == "preparation"
    assert release["submission_status"] == "not_submitted"
    assert release["publication_status"] == "not_published"
    assert release["doi_status"] == "not_minted_for_dataset_paper_release"


def test_research_release_preserves_temporal_and_licensing_governance():
    release = _load(RELEASE)
    integrity = release["scientific_integrity"]
    assert integrity["missing_values_preserved"] is True
    assert integrity["unsupported_temporal_links_remain_unmatched"] is True
    assert integrity["historical_and_current_geography_kept_distinct"] is True
    assert integrity["person_level_data_in_release"] is False
    assert integrity["third_party_licensing_preserved_separately"] is True
