from pathlib import Path

import polars as pl
import pytest

from modules.health_access.ingest_facilities import curate_facility_directory


def _write_core(path: Path) -> None:
    pl.DataFrame(
        {
            "place_id": ["census2011:district:001", "census2011:district:002"],
            "place_type": ["district", "district"],
            "name": ["Ranchi", "Khunti"],
            "district_code": ["001", "002"],
        }
    ).write_csv(path)


def _write_source(path: Path, *, bad_district: bool = False, missing_id: bool = False) -> None:
    pl.DataFrame(
        {
            "State": ["Jharkhand", "Bihar", "Jharkhand"],
            "District": ["Ranchi", "Patna", "Unknown" if bad_district else "Khunti"],
            "RecordID": ["JH001", "BR001", "" if missing_id else "JH002"],
            "Hospital": ["Alpha Hospital", "Beta Hospital", "Gamma CHC"],
            "Category": ["Hospital", "Hospital", "CHC"],
            "Ownership": ["Government", "Private", "Government"],
            "Address": ["A", "B", "C"],
            "Lat": ["23.34", "25.61", ""],
            "Lon": ["85.31", "85.14", ""],
            "Medicine": ["Allopathic", "Allopathic", "Allopathic"],
        }
    ).write_csv(path)


def _curate(source: Path, core: Path, output: Path, *, geography_vintage: str = "census2011_compatible"):
    return curate_facility_directory(
        source,
        core,
        output,
        source_id="OGD_TEST",
        reference_period="2025-06-02",
        source_geography_vintage=geography_vintage,
        state_column="State",
        district_column="District",
        record_id_column="RecordID",
        name_column="Hospital",
        type_column="Category",
        ownership_column="Ownership",
        address_column="Address",
        latitude_column="Lat",
        longitude_column="Lon",
        systems_column="Medicine",
    )


def test_facility_ingest_filters_state_links_exactly_and_preserves_missing_coordinates(tmp_path: Path):
    core = tmp_path / "core.csv"
    source = tmp_path / "source.csv"
    output = tmp_path / "out.csv"
    _write_core(core)
    _write_source(source)

    stats = _curate(source, core, output)
    result = pl.read_csv(output, infer_schema_length=100)

    assert stats == {
        "input_rows": 3,
        "jharkhand_output_rows": 2,
        "skipped_other_states": 1,
        "unmatched_districts": 0,
    }
    assert result["source_record_id"].to_list() == ["JH001", "JH002"]
    assert result["district_code"].to_list() == [1, 2]
    assert result["latitude"].to_list()[1] is None
    assert result["longitude"].to_list()[1] is None
    assert set(result["source_geography_vintage"].to_list()) == {"census2011_compatible"}
    assert set(result["geographic_link_method"].to_list()) == {
        "unique_exact_normalized_name_to_census2011_district"
    }


def test_facility_ingest_rejects_unmatched_jharkhand_district(tmp_path: Path):
    core = tmp_path / "core.csv"
    source = tmp_path / "source.csv"
    output = tmp_path / "out.csv"
    _write_core(core)
    _write_source(source, bad_district=True)

    with pytest.raises(ValueError, match="failed exact Census-2011 linking"):
        _curate(source, core, output)
    assert not output.exists()


def test_facility_ingest_rejects_missing_source_identity(tmp_path: Path):
    core = tmp_path / "core.csv"
    source = tmp_path / "source.csv"
    output = tmp_path / "out.csv"
    _write_core(core)
    _write_source(source, missing_id=True)

    with pytest.raises(ValueError, match="source-provided facility record identifier"):
        _curate(source, core, output)
    assert not output.exists()


def test_facility_ingest_rejects_current_geography_without_temporal_crosswalk(tmp_path: Path):
    core = tmp_path / "core.csv"
    source = tmp_path / "source.csv"
    output = tmp_path / "out.csv"
    _write_core(core)
    _write_source(source)

    with pytest.raises(ValueError, match="evidence-backed temporal crosswalk"):
        _curate(source, core, output, geography_vintage="current_2026")
    assert not output.exists()
