from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "modules" / "health_access" / "acquisition_evidence" / "2026-09-12_nfhs5_iips_discovery_surface.yaml"


def load_evidence():
    return yaml.safe_load(EVIDENCE.read_text(encoding="utf-8"))


def test_iips_nfhs5_discovery_surface_is_authoritative_but_not_payload():
    data = load_evidence()
    page = data["official_page"]
    observed = data["observation"]
    rules = set(data["rules"])

    assert "iipsindia.ac.in" in page["url"]
    assert page["page_updated_as_displayed"] == "2026-09-10"
    assert "rchiips.org/nfhs/factsheet_NFHS-5.shtml" in page["linked_nfhs5_fact_sheet_index"]
    assert observed["page_confirms_nfhs5_fact_sheet_index"] is True
    assert observed["direct_jharkhand_payload_identity_observed"] is False
    assert observed["raw_payload_acquired"] is False
    assert observed["sha256"] is None
    assert observed["schema_inspected"] is False
    assert data["publication_allowed"] is False
    assert "never convert missing to zero" in data["missing_value_rule"]
    assert "discovery_surface_is_not_payload" in rules
    assert "state_fact_sheet_is_not_district_workbook" in rules
    assert "never_construct_unobserved_asset_url" in rules
