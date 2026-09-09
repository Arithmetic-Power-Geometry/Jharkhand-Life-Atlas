from pathlib import Path

import pytest

from scripts.acquire_nfhs5_district_factsheet import sha256_file, validate_authoritative_url


def test_nfhs5_acquisition_accepts_only_official_https_excel_urls():
    validate_authoritative_url(
        "https://data.gov.in/files/ogdpv2dms/s3fs-public/datafile/NFHS_5_India_Districts_Factsheet_Data.xls"
    )
    with pytest.raises(ValueError):
        validate_authoritative_url("http://data.gov.in/file.xls")
    with pytest.raises(ValueError):
        validate_authoritative_url("https://example.org/file.xls")
    with pytest.raises(ValueError):
        validate_authoritative_url("https://data.gov.in/file.csv")


def test_sha256_file_is_deterministic(tmp_path: Path):
    payload = tmp_path / "sample.xls"
    payload.write_bytes(b"jla-nfhs5-test")
    assert sha256_file(payload) == "16d7da4462613093987cecfda5024603f00137fcea6a833acdbe49353adecc34"
