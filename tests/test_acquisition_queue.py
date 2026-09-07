from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
QUEUE = ROOT / "config" / "acquisition_queue.yaml"


def load_queue():
    return yaml.safe_load(QUEUE.read_text(encoding="utf-8"))


def test_health_remains_highest_priority_and_ranks_are_unique():
    data = load_queue()
    workstreams = data["workstreams"]
    ranks = [item["rank"] for item in workstreams]
    assert ranks == sorted(ranks)
    assert len(ranks) == len(set(ranks))
    assert workstreams[0]["module_id"] == "health_access"


def test_priority_modules_are_present():
    data = load_queue()
    modules = {item["module_id"] for item in data["workstreams"]}
    assert {"health_access", "water_access", "sanitation_hygiene", "education_access"} <= modules


def test_discovery_queue_never_marks_unacquired_work_as_publishable():
    data = load_queue()
    for item in data["workstreams"]:
        assert item["publication_allowed"] is False
        assert item["next_evidence"]


def test_queue_preserves_core_governance_rules():
    rules = set(load_queue()["execution_rules"])
    assert "preserve_missing_as_null" in rules
    assert "never_use_name_only_temporal_geography_equivalence" in rules
    assert "never_collect_or_publish_sensitive_person_level_data" in rules
    assert "every_successful_acquisition_must_satisfy_JLA_SOURCE_SNAPSHOT_V1" in rules
