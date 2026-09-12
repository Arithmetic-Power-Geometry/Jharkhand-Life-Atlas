from modules.health_access.acquire_hmis_quarterly_facility_extremes import (
    CATALOG_ID,
    classify_observed_response,
    extract_catalog_acquisition_controls,
)


def test_disabled_catalog_api_and_zip_controls_are_authoritative_negative_evidence():
    html = f"""
    <html><head><title>Official OGD catalog</title></head><body>
      <a href=\"/apis/{CATALOG_ID}\" aria-disabled=\"true\" class=\"btn disabled\">
        Catalog API is not available
      </a>
      <a href=\"#\" aria-disabled=\"true\" class=\"btn disabled\">
        Zip Download is not available
      </a>
    </body></html>
    """
    controls = extract_catalog_acquisition_controls(html)
    assert controls["catalog_api_control_present"] is True
    assert controls["catalog_api_available"] is False
    assert controls["zip_download_control_present"] is True
    assert controls["zip_download_available"] is False
    assert controls["authoritative_machine_download_control_available"] is False
    assert controls["authoritative_controls_explicitly_block_acquisition"] is True


def test_enabled_control_is_only_recorded_as_available_not_as_resource_identity():
    html = f"""
    <html><body>
      <a href=\"/apis/{CATALOG_ID}\">Catalog API</a>
      <a href=\"/download/catalog.zip\">Zip Download</a>
    </body></html>
    """
    observed = classify_observed_response(html.encode(), "text/html")
    assert observed["catalog_api_available"] is True
    assert observed["zip_download_available"] is True
    assert observed["authoritative_machine_download_control_available"] is True
    assert observed["machine_resource_identity_resolved"] is False
    assert observed["observed_schema_available"] is False


def test_placeholder_or_disabled_href_cannot_be_promoted_to_available_download():
    html = """
    <html><body>
      <a href=\"#\">Catalog API</a>
      <a href=\"javascript:void(0)\" class=\"disabled\">Zip Download</a>
    </body></html>
    """
    controls = extract_catalog_acquisition_controls(html)
    assert controls["catalog_api_available"] is False
    assert controls["zip_download_available"] is False
    assert controls["authoritative_machine_download_control_available"] is False


def test_catalog_uuid_remains_excluded_from_child_resource_candidates():
    html = f"""
    <html><body>
      <a href=\"/apis/{CATALOG_ID}\" aria-disabled=\"true\">Catalog API is not available</a>
    </body></html>
    """
    observed = classify_observed_response(html.encode(), "text/html")
    assert CATALOG_ID in observed["observed_uuids"]
    assert observed["explicit_resource_uuid_candidates"] == []
    assert observed["machine_resource_identity_resolved"] is False
