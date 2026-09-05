from pathlib import Path

from jla.data import CORE_DIR, core_research_tables
from jla.modules import discover_modules


REQUIRED_MODULE1_TABLES = {
    "census_places_2011.csv",
    "village_demography_2011.csv",
    "village_amenities_2011.csv",
    "census_mdds_crosswalk_2001_2011.csv",
    "census_lgd_temporal_crosswalk.csv",
    "lgd_districts_current.csv",
    "lgd_subdistricts_current.csv",
    "lgd_blocks_current.csv",
    "lgd_panchayats_current.csv",
    "lgd_villages_current.csv",
    "pca_source_manifest_2011.csv",
    "source_coverage.csv",
}


def test_module1_required_curated_outputs_exist():
    missing = sorted(name for name in REQUIRED_MODULE1_TABLES if not (CORE_DIR / name).exists())
    assert missing == []


def test_module1_research_bundle_inventory_exposes_required_tables():
    assert REQUIRED_MODULE1_TABLES.issubset(set(core_research_tables()))


def test_module1_contract_is_complete():
    module = next(m for m in discover_modules() if m.get("id") == "core_geography")
    assert module.get("_valid") is True
    assert module.get("status") == "complete"
    assert module.get("coverage", {}).get("full_village_ingest") == "complete_authoritative_available_layers"
