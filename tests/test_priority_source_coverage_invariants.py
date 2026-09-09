import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CANONICAL_COVERAGE_MODULES = (
    "health_access",
    "water_access",
    "sanitation_hygiene",
    "education_access",
    "agriculture_farmers",
    "nutrition_food_security",
    "maternal_child_health",
    "livelihood_employment_poverty",
    "roads_transport_accessibility",
    "banking_financial_access",
    "digital_connectivity",
    "electricity_energy",
    "forest_land_cover",
    "drought_water_stress",
    "markets_essential_services",
    "weather_climate",
)
PRIORITY_MODULES = CANONICAL_COVERAGE_MODULES[:4]
NONPUBLIC_PREFIXES = ("pending", "blocked", "catalog")
REQUIRED_COLUMNS = {
    "source_id",
    "catalog_or_resource_verified",
    "raw_file_ingested",
    "curated_output_published",
    "publication_status",
    "notes",
}


def _rows(module: str):
    path = ROOT / "modules" / module / "source_coverage.csv"
    assert path.exists(), f"missing canonical source coverage for module: {module}"
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        assert REQUIRED_COLUMNS.issubset(set(reader.fieldnames or [])), (
            module,
            "canonical source coverage is missing required evidence-state columns",
        )
        yield from reader


def test_priority_modules_keep_source_coverage():
    for module in PRIORITY_MODULES:
        assert (ROOT / "modules" / module / "source_coverage.csv").exists(), (
            f"missing source coverage for priority module: {module}"
        )


def test_canonical_source_coverage_is_fail_closed():
    """Discovery, acquisition, and publication must remain distinct states."""
    for module in CANONICAL_COVERAGE_MODULES:
        for row in _rows(module):
            source_id = row["source_id"]
            verified = row["catalog_or_resource_verified"].strip().lower()
            ingested = row["raw_file_ingested"].strip().lower()
            published = row["curated_output_published"].strip().lower()
            status = row["publication_status"].strip().lower()

            assert verified in {"yes", "no"}, (module, source_id, "invalid verified flag")
            assert ingested in {"yes", "no"}, (module, source_id, "invalid ingestion flag")
            assert published in {"yes", "no"}, (module, source_id, "invalid publication flag")

            if published == "yes":
                assert verified == "yes", (module, source_id, "published without verified source")
                assert ingested == "yes", (module, source_id, "published without acquired raw evidence")

            if ingested == "no":
                assert published == "no", (module, source_id, "unacquired source exposed as published")

            if status.startswith(NONPUBLIC_PREFIXES):
                assert published == "no", (module, source_id, f"nonpublic status exposed: {status}")


def test_canonical_source_coverage_has_explicit_blocker_for_unpublished_sources():
    """Unpublished canonical coverage rows must explain why they remain closed."""
    for module in CANONICAL_COVERAGE_MODULES:
        for row in _rows(module):
            if row["curated_output_published"].strip().lower() == "no":
                assert row["publication_status"].strip(), (module, row["source_id"], "missing publication status")
                assert row["notes"].strip(), (module, row["source_id"], "missing blocker/method note")
