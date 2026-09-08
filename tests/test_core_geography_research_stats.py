from modules.core_geography.research_stats import build_statistics


def test_research_statistics_are_artifact_derived_and_fail_safe():
    stats = build_statistics()
    assert stats["census_2011"]["place_rows"] > 0
    assert stats["census_2011"]["district_codes"] == 24
    assert stats["current_lgd"]["district_rows"] == 24
    assert stats["current_lgd"]["village_rows"] > 0
    assert stats["crosswalks"]["census_2001_2011_rows"] > 0
    assert stats["crosswalks"]["census_2011_lgd_temporal_rows"] > 0
    assert stats["integrity"]["missing_values_preserved"] is True
    assert stats["integrity"]["name_only_temporal_equivalence_inferred"] is False
    assert stats["integrity"]["person_level_data_used"] is False
