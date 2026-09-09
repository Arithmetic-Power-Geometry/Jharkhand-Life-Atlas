import csv
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PRIORITY_MODULES = (
    "health_access",
    "water_access",
    "sanitation_hygiene",
    "education_access",
)
NONPUBLIC_PREFIXES = ("pending", "blocked", "catalog")


def _coverage_modules():
    """Return every module that opts into explicit source-coverage reporting."""
    modules_root = ROOT / "modules"
    return tuple(sorted(path.parent.name for path in modules_root.glob("*/source_coverage.csv")))


def _rows(module: str):
    path = ROOT / "modules" / module / "source_coverage.csv"
    assert path.exists(), f"missing source coverage for module: {module}"
    with path.open(newline="", encoding="utf-8") as handle:
        yield from csv.DictReader(handle)


def test_priority_modules_keep_source_coverage():
    coverage_modules = set(_coverage_modules())
    for module in PRIORITY_MODULES:
        assert module in coverage_modules, f"missing source coverage for priority module: {module}"


def test_all_reported_source_coverage_is_fail_closed():
    """Discovery, acquisition, and publication must remain distinct states everywhere."""
    for module in _coverage_modules():
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


def test_all_reported_source_coverage_has_explicit_blocker_for_unpublished_sources():
    """Unpublished sources must explain why they remain closed."""
    for module in _coverage_modules():
        for row in _rows(module):
            if row["curated_output_published"].strip().lower() == "no":
                assert row["publication_status"].strip(), (module, row["source_id"], "missing publication status")
                assert row["notes"].strip(), (module, row["source_id"], "missing blocker/method note")
