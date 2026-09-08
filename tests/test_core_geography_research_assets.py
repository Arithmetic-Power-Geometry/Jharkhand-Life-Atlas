import csv
import json

from modules.core_geography.research_assets import write_assets


def test_research_assets_are_reproducible_and_vintage_explicit(tmp_path):
    paths = write_assets(tmp_path)

    stats = json.loads(paths["statistics"].read_text(encoding="utf-8"))
    semantics = json.loads(paths["semantics"].read_text(encoding="utf-8"))
    with paths["figure"].open(encoding="utf-8", newline="") as handle:
        figure_rows = list(csv.DictReader(handle))
    with paths["table"].open(encoding="utf-8", newline="") as handle:
        table_rows = list(csv.DictReader(handle))

    assert stats["census_2011"]["district_codes"] == 24
    assert stats["current_lgd"]["district_rows"] == 24
    assert table_rows
    assert figure_rows
    assert {row["geography_vintage"] for row in figure_rows} == {"census_2011", "current_lgd"}
    assert all(row["cross_vintage_equivalence_asserted"] == "False" for row in figure_rows)
    assert semantics["missing_values_imputed"] is False
    assert semantics["cross_vintage_equivalence_inferred"] is False
    assert semantics["person_level_data_used"] is False


def test_research_asset_generation_is_byte_deterministic(tmp_path):
    first = write_assets(tmp_path / "a")
    second = write_assets(tmp_path / "b")
    for key in first:
        assert first[key].read_bytes() == second[key].read_bytes()
