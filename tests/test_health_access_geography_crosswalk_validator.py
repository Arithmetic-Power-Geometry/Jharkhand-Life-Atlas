from pathlib import Path

import polars as pl
import pytest

from modules.health_access.validate_geography_crosswalk import validate_crosswalk


def _core(path: Path) -> None:
    pl.DataFrame({"place_type": ["district", "district"], "district_code": [1, 2]}).write_csv(path)


def _crosswalk(path: Path, *, relationship: str = "equivalent", review_status: str = "verified_equivalent") -> None:
    pl.DataFrame(
        {
            "source_geography_vintage": ["current_2026", "current_2026"],
            "source_district_name": ["Ranchi", "Khunti"],
            "source_district_code": ["101", None],
            "census2011_district_code": ["1", "2"],
            "relationship": [relationship, "equivalent"],
            "evidence_source_id": ["AUTH_GEO", "AUTH_GEO"],
            "evidence_url": ["https://example.gov.in/a", "https://example.gov.in/b"],
            "evidence_reference_date": ["2026-08-01", "2026-08-01"],
            "reviewed_on": ["2026-09-06", "2026-09-06"],
            "review_status": [review_status, "verified_equivalent"],
            "notes": [None, None],
        }
    ).write_csv(path)


def test_verified_crosswalk_passes_and_preserves_null_source_code(tmp_path: Path):
    core = tmp_path / "core.csv"
    crosswalk = tmp_path / "crosswalk.csv"
    _core(core)
    _crosswalk(crosswalk)
    stats = validate_crosswalk(crosswalk, core, source_geography_vintage="current_2026")
    assert stats == {"rows": 2, "verified_equivalent_rows": 2, "unique_source_districts": 2}
    assert pl.read_csv(crosswalk)["source_district_code"].to_list()[1] is None


def test_non_equivalent_geography_fails_closed(tmp_path: Path):
    core = tmp_path / "core.csv"
    crosswalk = tmp_path / "crosswalk.csv"
    _core(core)
    _crosswalk(crosswalk, relationship="boundary_change", review_status="non_equivalent")
    with pytest.raises(ValueError, match="split/merge/boundary-change/unresolved"):
        validate_crosswalk(crosswalk, core, source_geography_vintage="current_2026")


def test_wrong_vintage_fails_closed(tmp_path: Path):
    core = tmp_path / "core.csv"
    crosswalk = tmp_path / "crosswalk.csv"
    _core(core)
    _crosswalk(crosswalk)
    with pytest.raises(ValueError, match="different source geography vintage"):
        validate_crosswalk(crosswalk, core, source_geography_vintage="current_2025")
