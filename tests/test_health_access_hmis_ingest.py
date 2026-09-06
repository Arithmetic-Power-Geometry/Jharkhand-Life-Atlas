from pathlib import Path

import polars as pl
import pytest

from modules.health_access.ingest_hmis import curate_hmis_district_csv


def _write_core(path: Path) -> None:
    pl.DataFrame(
        [
            {"place_id": "census2011:district:01", "place_type": "district", "name": "Ranchi", "district_code": "364"},
            {"place_id": "census2011:district:02", "place_type": "district", "name": "Khunti", "district_code": "365"},
        ]
    ).write_csv(path)


def test_hmis_exact_district_link_and_missing_not_zero(tmp_path: Path) -> None:
    core = tmp_path / "core.csv"
    source = tmp_path / "hmis.csv"
    output = tmp_path / "out.csv"
    _write_core(core)
    pl.DataFrame(
        [
            {"District": "Ranchi", "Indicator": "Institutional deliveries", "Value": "12"},
            {"District": "Khunti", "Indicator": "Institutional deliveries", "Value": "NA"},
        ]
    ).write_csv(source)

    stats = curate_hmis_district_csv(
        source,
        core,
        output,
        source_id="OGD_HMIS_JH_DISTRICT",
        period="2014-12",
        district_column="District",
        indicator_column="Indicator",
        value_column="Value",
        unit="count",
    )

    result = pl.read_csv(output)
    assert stats["output_rows"] == 2
    assert set(result["place_id"].to_list()) == {"census2011:district:01", "census2011:district:02"}
    assert result.filter(pl.col("source_geography_name") == "Khunti")["value_numeric"][0] is None
    assert set(result["geographic_link_method"].to_list()) == {"unique_exact_normalized_name_to_census2011_district"}


def test_hmis_refuses_unmatched_district_instead_of_fuzzy_link(tmp_path: Path) -> None:
    core = tmp_path / "core.csv"
    source = tmp_path / "hmis.csv"
    output = tmp_path / "out.csv"
    _write_core(core)
    pl.DataFrame([{"District": "Ranchi District", "Indicator": "ANC", "Value": "3"}]).write_csv(source)

    with pytest.raises(ValueError, match="no fuzzy/current-geography fallback"):
        curate_hmis_district_csv(
            source,
            core,
            output,
            source_id="OGD_HMIS_JH_DISTRICT",
            period="2014-12",
            district_column="District",
            indicator_column="Indicator",
            value_column="Value",
            unit="count",
        )


def test_hmis_refuses_non_numeric_values(tmp_path: Path) -> None:
    core = tmp_path / "core.csv"
    source = tmp_path / "hmis.csv"
    output = tmp_path / "out.csv"
    _write_core(core)
    pl.DataFrame([{"District": "Ranchi", "Indicator": "ANC", "Value": "suppressed"}]).write_csv(source)

    with pytest.raises(ValueError, match="Non-numeric HMIS value"):
        curate_hmis_district_csv(
            source,
            core,
            output,
            source_id="OGD_HMIS_JH_DISTRICT",
            period="2014-12",
            district_column="District",
            indicator_column="Indicator",
            value_column="Value",
            unit="count",
        )
