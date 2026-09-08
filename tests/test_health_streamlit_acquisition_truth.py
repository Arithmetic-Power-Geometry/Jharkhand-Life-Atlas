from jla.acquisition import health_resource_identities, health_resource_identity_status


def test_health_identity_status_is_fail_closed_until_payloads_are_verified():
    status = health_resource_identity_status()
    assert status["resource_count"] >= 2
    assert status["raw_payloads_acquired"] == 0
    assert status["publishable_resources"] == 0


def test_health_identity_table_preserves_unresolved_machine_ids_as_null():
    frame = health_resource_identities()
    assert frame.height >= 2
    rows = frame.to_dicts()
    for row in rows:
        if row["machine_payload_state"] == "unresolved":
            assert row["machine_resource_id"] is None
            assert row["raw_payload_acquired"] is False
            assert row["publication_allowed"] is False


def test_health_identity_table_exposes_official_resource_urls_only():
    for row in health_resource_identities().to_dicts():
        assert row["resource_url"].startswith("https://")
