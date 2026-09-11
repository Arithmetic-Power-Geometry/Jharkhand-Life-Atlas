from pathlib import Path


def test_reports_page_uses_provenance_gated_historical_thematic_evidence():
    source = Path("app_pages/reports.py").read_text(encoding="utf-8")

    # The report page may advertise thematic evidence only after the same immutable
    # provenance gate used by Research downloads has passed.
    assert 'meta.get("status") != "validated_source_native_historical_extract"' in source
    assert 'int(meta.get("reference_year", 0)) != 2011' in source
    assert 'meta.get("output") != str(csv_path)' in source
    assert 'not meta.get("output_sha256") or not meta.get("source_sha256")' in source

    for slug in (
        "health_access",
        "water_access",
        "sanitation_hygiene",
        "education_access",
    ):
        assert slug in source

    # Report metadata must keep historical evidence separate from present-day status
    # and must not authorize name-only historical/current geography equivalence.
    assert "does not imply current service status" in source
    assert "does not authorize Census-2011/current-LGD equivalence" in source
    assert "never joins thematic values" in source
