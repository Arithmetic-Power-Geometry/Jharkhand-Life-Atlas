from jla.ogd_identity import classify_ogd_url, explicit_machine_resource_id


def test_catalog_api_id_is_not_machine_resource_id():
    url = "https://www.data.gov.in/apis/e48a8bcf-ff56-4f39-839d-095827ba2a18"
    identity = classify_ogd_url(url)
    assert identity.official_host is True
    assert identity.identity_kind == "catalog_api"
    assert identity.explicit_id == "e48a8bcf-ff56-4f39-839d-095827ba2a18"
    assert identity.machine_payload_endpoint is False
    assert explicit_machine_resource_id(url) is None


def test_explicit_api_resource_uuid_is_machine_candidate_only_when_observed():
    url = "https://api.data.gov.in/resource/123e4567-e89b-42d3-a456-426614174000?format=json"
    identity = classify_ogd_url(url)
    assert identity.identity_kind == "machine_resource_candidate"
    assert identity.machine_payload_endpoint is True
    assert explicit_machine_resource_id(url) == "123e4567-e89b-42d3-a456-426614174000"


def test_resource_page_does_not_become_machine_endpoint():
    url = "https://www.data.gov.in/resource/123e4567-e89b-42d3-a456-426614174000"
    identity = classify_ogd_url(url)
    assert identity.identity_kind == "resource_page"
    assert identity.machine_payload_endpoint is False
    assert explicit_machine_resource_id(url) is None


def test_slug_or_title_never_generates_identifier():
    url = "https://www.data.gov.in/resource/national-hospital-directory-geo-code-and-additional-parameters"
    identity = classify_ogd_url(url)
    assert identity.identity_kind == "resource_page"
    assert identity.explicit_id is None
    assert explicit_machine_resource_id(url) is None


def test_non_official_host_is_rejected():
    identity = classify_ogd_url(
        "https://example.org/resource/123e4567-e89b-42d3-a456-426614174000"
    )
    assert identity.official_host is False
    assert identity.identity_kind == "untrusted_or_invalid"
    assert identity.explicit_id is None
    assert explicit_machine_resource_id(identity.url) is None
