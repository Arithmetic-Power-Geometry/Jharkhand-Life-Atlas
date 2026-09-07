from jla.acquisition import acquisition_queue, acquisition_queue_status


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
