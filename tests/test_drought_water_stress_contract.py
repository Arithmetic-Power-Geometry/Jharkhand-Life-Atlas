from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "modules" / "drought_water_stress"


def _yaml(name):
    return yaml.safe_load((MODULE / name).read_text(encoding="utf-8"))


def test_module17_is_fail_closed_and_dependency_safe():
    module = _yaml("module.yaml")
    assert module["id"] == "drought_water_stress"
    assert module["status"] == "active"
    assert module["dependencies"] == ["core_geography"]
    assert module["engineering"]["fuzzy_linking"] == "prohibited"
    assert module["engineering"]["missing_numeric_policy"] == "preserve_null_never_zero"
    assert "silently" in module["engineering"]["temporal_geography_policy"].lower()
    assert "meteorological_agricultural_hydrological_drought_are_distinct" in module["principles"]
    assert "do not publish" in module["engineering"]["composite_policy"].lower()


def test_module17_publication_gate_starts_closed():
    gate = _yaml("completion_gate.yaml")
    assert gate["publication_ready"] is False
    required = {
        "authoritative_acquisition", "rights_review", "geographic_linkage",
        "provenance", "production_schema", "indicators", "validation", "tests",
        "streamlit", "downloads_reports", "documentation", "green_ci_main",
    }
    assert required.issubset(gate["requirements"])
    assert all(gate["requirements"][key]["passed"] is False for key in required)


def test_module17_sources_do_not_claim_unacquired_payloads():
    sources = _yaml("sources.yaml")
    assert sources["status"] == "discovery_active_no_thematic_values_published"
    text = (MODULE / "sources.yaml").read_text(encoding="utf-8").lower()
    assert "not_yet_acquired" in text or "not_yet_selected" in text
    assert "pending" in text
    assert "blocked" in text


def test_module17_forbids_false_precision_and_missing_as_zero():
    module = _yaml("module.yaml")
    assert module["scope"]["village_estimates"].startswith("prohibited")
    assert module["engineering"]["missing_numeric_policy"] == "preserve_null_never_zero"
    gate_text = (MODULE / "completion_gate.yaml").read_text(encoding="utf-8").lower()
    assert "missing to zero" in gate_text
    assert "meteorological, agricultural and hydrological" in gate_text
