from modules.health_access.resolve_ogd_hospital_resource_identity import (
    TARGETS,
    _explicit_official_payload_urls,
    _explicit_resource_url_uuids,
    _is_target_page,
)


def test_decodes_escaped_official_resource_uuid_without_constructing_it():
    rid = "123e4567-e89b-42d3-a456-426614174000"
    text = (
        'window.__DATA__={"url":"https:\\u002F\\u002Fapi.data.gov.in'
        f'\\u002Fresource\\u002F{rid}"}}'
    )
    assert _explicit_resource_url_uuids(text) == [rid]


def test_decodes_escaped_official_csv_url():
    text = (
        'window.__DATA__={"download":"https:\\/\\/www.data.gov.in\\/files\\/'
        'hospital_directory.csv"}'
    )
    assert _explicit_official_payload_urls(text) == [
        "https://www.data.gov.in/files/hospital_directory.csv"
    ]


def test_rejects_escaped_third_party_payload_url():
    text = (
        'window.__DATA__={"download":"https:\\u002F\\u002Fexample.org'
        '\\u002Fhospital_directory.csv"}'
    )
    assert _explicit_official_payload_urls(text) == []


def test_catalog_uuid_is_still_excluded_after_escape_normalization():
    catalog_id = "e48a8bcf-ff56-4f39-839d-095827ba2a18"
    text = (
        'window.__DATA__={"url":"https:\\u002F\\u002Fapi.data.gov.in'
        f'\\u002Fresource\\u002F{catalog_id}"}}'
    )
    assert _explicit_resource_url_uuids(text) == []


def test_plural_resources_surface_is_canonical_target_evidence():
    target = TARGETS["OGD_NHP_HOSPITAL_GEO_2026"]
    page = {
        "requested_url": (
            "https://data.gov.in/resources/"
            "national-hospital-directory-geo-code-and-additional-parameters-updated-till-last-month"
        ),
        "final_url": (
            "https://www.data.gov.in/resources/"
            "national-hospital-directory-geo-code-and-additional-parameters-updated-till-last-month"
        ),
    }
    assert _is_target_page(page, target)


def test_both_priority_targets_probe_singular_and_plural_official_surfaces():
    for target in TARGETS.values():
        paths = {"/resource/" if "/resource/" in url else "/resources/" for url in target["resource_urls"]}
        assert paths == {"/resource/", "/resources/"}
        assert any(url.startswith("https://www.data.gov.in/") for url in target["resource_urls"])
        assert any(url.startswith("https://data.gov.in/") for url in target["resource_urls"])
