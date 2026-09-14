from jla.acquisition import (
    acquisition_queue,
    acquisition_queue_status,
    health_resource_identities,
    health_resource_identity_status,
)


def test_acquisition_queue_exposes_repository_truth_without_publication_inference():
    frame = acquisition_queue()
    assert frame.height >= 4
    assert frame["priority"].to_list() == sorted(frame["priority"].to_list())
    assert frame.row(0, named=True)["module"] == "health_access"
    assert frame.row(0, named=True)["publication_allowed"] is False
    assert "evidence_remaining" in frame.columns


def test_acquisition_queue_status_preserves_controlled_parallel_rules():
    status = acquisition_queue_status()
    assert status["status"] == "active"
    assert status["workstream_count"] >= 4
    rules = set(status["execution_rules"])
    assert "health_access_has_highest_priority" in rules
    assert "never_publish_from_catalog_or_dashboard_metadata_alone" in rules
    assert "preserve_missing_as_null" in rules
    assert "never_use_name_only_temporal_geography_equivalence" in rules


def test_health_resource_identity_view_reflects_verified_primary_bytes_but_fails_closed():
    frame = health_resource_identities()
    status = health_resource_identity_status()

    assert status["registry_id"] == "JLA_HEALTH_RESOURCE_IDENTITY_V2"
    assert status["resource_count"] == frame.height
    assert status["resource_count"] >= 2
    assert status["machine_identities_resolved"] == 0
    assert status["raw_payloads_acquired"] == 1
    assert status["official_payload_bindings_verified"] == 1
    assert status["publishable_resources"] == 0

    assert frame["source"].to_list() == [
        "OGD_NIN_HEALTH_FACILITIES_GEO_2026",
        "OGD_NHP_HOSPITAL_GEO_2026",
    ]
    assert frame["machine_resource_id"].null_count() == frame.height
    assert frame["raw_payload_acquired"].to_list() == [False, True]
    assert frame["official_payload_binding_verified"].to_list() == [False, True]
    assert frame["publication_allowed"].to_list() == [False] * frame.height

    bound = frame.filter(frame["official_payload_binding_verified"]).row(0, named=True)
    assert bound["raw_sha256"] == "1ddcad9f9b922142a4374c7b89b70fb6cefd8a257448c70a61e1c07d98845134"
    assert bound["raw_bytes"] == 10341256
    assert bound["schema_inspected"] is False


def test_verified_official_bytes_do_not_imply_machine_identity_or_publication():
    frame = health_resource_identities()
    bound = frame.filter(frame["official_payload_binding_verified"]).row(0, named=True)
    assert bound["machine_resource_id"] is None
    assert "unresolved" in bound["machine_payload_state"]
    assert bound["publication_allowed"] is False


def test_health_resource_identity_view_exposes_only_authoritative_resource_urls():
    frame = health_resource_identities()
    urls = frame["resource_url"].to_list()
    assert urls
    assert all(url.startswith("https://") for url in urls)
    assert all("data.gov.in/" in url for url in urls)
    assert all("api.data.gov.in/resource/" not in url for url in urls)
