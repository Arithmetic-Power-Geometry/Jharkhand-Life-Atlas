from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "modules" / "sanitation_hygiene" / "module.yaml"
SOURCES = ROOT / "modules" / "sanitation_hygiene" / "sources.yaml"


def _load(path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_sanitation_module_is_active_not_complete_before_publication_gate():
    module = _load(MODULE)
    assert module["id"] == "sanitation_hygiene"
    assert module["status"] == "active"
    assert module["dependencies"] == ["core_geography"]
    assert "Do not mark complete" in module["completion_gate"]


def test_sanitation_scientific_safeguards_are_explicit():
    module = _load(MODULE)
    principles = set(module["principles"])
    assert "missing_is_not_zero" in principles
    assert "no_person_level_or_household_identifiers" in principles
    assert "historical_and_current_geographies_not_silently_merged" in principles
    assert module["engineering"]["fuzzy_linking"] == "prohibited"
    assert module["engineering"]["missing_numeric_policy"] == "preserve_null_never_zero"


def test_discovered_sources_remain_nonpublishable_until_exact_payload_review():
    sources = _load(SOURCES)["sources"]
    assert sources
    for source in sources:
        assert source["publishable"] is False
        assert source["authority"]
        assert source["url"].startswith("https://")
        assert "acquisition_status" in source
    ogd = next(s for s in sources if s["id"] == "OGD_SBMG_RURAL_SANITATION_COVERAGE")
    assert ogd["acquisition_status"] == "catalog_verified_exact_resource_payload_pending"
