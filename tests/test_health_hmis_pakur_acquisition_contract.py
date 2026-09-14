import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "modules" / "health_access" / "acquire_ogd_hmis_pakur_2019_20_november.py"


def _module():
    spec = importlib.util.spec_from_file_location("health_hmis_pakur_acquisition", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_hmis_pakur_contract_has_explicit_period_and_provisional_semantics():
    text = SCRIPT.read_text(encoding="utf-8")

    assert '"reference_period": "2019-20_november"' in text
    assert '"provisional_figures": True' in text
    assert '"aggregation_semantics"' in text
    assert '"publication_allowed": False' in text


def test_candidate_links_reject_non_ogd_hosts_and_resource_page_itself():
    module = _module()
    html = f'''
    <a href="{module.RESOURCE_PAGE}">same page</a>
    <a href="https://evil.example/download.csv">external csv</a>
    <a href="https://www.data.gov.in/files/example.csv">official csv</a>
    '''

    links = module.candidate_links(html)

    assert "https://www.data.gov.in/files/example.csv" in links
    assert module.RESOURCE_PAGE not in links
    assert all("evil.example" not in link for link in links)


def test_csv_inspection_rejects_html_masquerading_as_data():
    module = _module()
    result = module.inspect_csv(
        b"<!doctype html><html><body>not csv</body></html>",
        "text/html; charset=utf-8",
        "https://www.data.gov.in/files/example.csv",
    )

    assert result["accepted"] is False
    assert result["reason"] == "html_not_data"


def test_csv_inspection_rejects_schema_without_authoritative_fields():
    module = _module()
    result = module.inspect_csv(
        b"Indicator,Wrong\nA,1\n",
        "text/csv",
        "https://www.data.gov.in/files/example.csv",
    )

    assert result["accepted"] is False
    assert result["reason"] == "schema_does_not_match_authoritative_resource_metadata"
    assert result["missing_expected_columns"]


def test_csv_inspection_accepts_only_complete_authoritative_schema():
    module = _module()
    header = ",".join(module.EXPECTED_COLUMNS)
    row = ",".join(["x"] * len(module.EXPECTED_COLUMNS))
    result = module.inspect_csv(
        f"{header}\n{row}\n".encode("utf-8"),
        "text/csv",
        "https://www.data.gov.in/files/example.csv",
    )

    assert result["accepted"] is True
    assert result["format"] == "csv"
    assert result["authoritative_schema_fields_verified"] == module.EXPECTED_COLUMNS


def test_source_contract_forbids_downscaling_and_requires_validation_gates():
    text = SCRIPT.read_text(encoding="utf-8")

    assert "subdistrict_aggregates_never_allocated_to_villages_facilities_or_persons" in text
    assert "preserve_missing_as_null" in text
    assert "provisional_source_status_must_be_preserved" in text
    assert "publication_requires_period_indicator_geography_and_validation_gates" in text
