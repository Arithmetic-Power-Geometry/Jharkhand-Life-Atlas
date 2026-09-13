from jla.geography_crosswalk import (
    accepted_records,
    audit_source_identifier_pairs,
    validate_crosswalk_record,
)


def valid_record():
    return {
        "source_code": "C2011-001",
        "source_vintage": "Census-2011",
        "target_code": "LGD-001",
        "target_vintage": "LGD-2026-09-08",
        "relation": "same_unit",
        "evidence_url": "https://lgdirectory.gov.in/example-authoritative-record",
        "evidence_date": "2026-09-08",
        "evidence_sha256": "a" * 64,
        "evidence_statement": "Authoritative record explicitly establishes continuity.",
        "evidence_reference_id": "example-only-test-reference",
        "source_name": "Example Village",
        "target_name": "Example Village",
    }


def test_accepts_explicit_authoritative_cross_vintage_evidence():
    decision = validate_crosswalk_record(valid_record())
    assert decision.accepted is True


def test_equal_names_alone_never_establish_equivalence():
    record = valid_record()
    record.pop("evidence_url")
    record.pop("evidence_date")
    record.pop("evidence_sha256")
    record.pop("evidence_statement")
    record.pop("evidence_reference_id")
    decision = validate_crosswalk_record(record)
    assert decision.accepted is False
    assert decision.reason == "authoritative_evidence_url_required"


def test_non_government_evidence_is_rejected():
    record = valid_record()
    record["evidence_url"] = "https://example.org/mapping"
    assert validate_crosswalk_record(record).accepted is False


def test_same_vintage_is_not_crosswalked():
    record = valid_record()
    record["target_vintage"] = record["source_vintage"]
    assert validate_crosswalk_record(record).reason == "crosswalk_requires_distinct_vintages"


def test_same_unit_requires_explicit_reference_id():
    record = valid_record()
    record.pop("evidence_reference_id")
    assert validate_crosswalk_record(record).reason == "same_unit_requires_evidence_reference_id"


def test_evidence_date_must_be_real_iso_calendar_date():
    record = valid_record()
    record["evidence_date"] = "2026-02-31"
    assert validate_crosswalk_record(record).reason == "evidence_date_must_be_iso_calendar_date"


def test_immutable_evidence_sha256_is_required():
    record = valid_record()
    record.pop("evidence_sha256")
    assert validate_crosswalk_record(record).reason == "evidence_sha256_required"

    record = valid_record()
    record["evidence_sha256"] = "not-a-sha256"
    assert validate_crosswalk_record(record).reason == "evidence_sha256_required"


def test_filter_never_promotes_invalid_records():
    good = valid_record()
    bad = valid_record()
    bad["target_code"] = "LGD-002"
    bad["evidence_url"] = "https://not-government.example/evidence"
    assert accepted_records([good, bad]) == [good]


def test_source_identifier_audit_accepts_only_internal_one_to_one_relation():
    audit = audit_source_identifier_pairs([
        ("101", "Ranchi"),
        ("102", "Khunti"),
        ("101", "RANCHI"),
    ])
    assert audit.safe_for_direct_linkage is True
    assert audit.reason == "internally_one_to_one_only_crosswalk_still_required"
    assert audit.distinct_identifier_count == 2
    assert audit.distinct_label_count == 2


def test_source_identifier_audit_rejects_one_id_with_multiple_labels():
    audit = audit_source_identifier_pairs([
        ("101", "Ranchi"),
        ("101", "Khunti"),
    ])
    assert audit.safe_for_direct_linkage is False
    assert audit.reason == "source_identifier_maps_to_multiple_labels"
    assert audit.identifiers_with_multiple_labels == ("101",)


def test_source_identifier_audit_rejects_one_label_with_multiple_ids():
    audit = audit_source_identifier_pairs([
        ("101", "Ranchi"),
        ("205", "Ranchi"),
    ])
    assert audit.safe_for_direct_linkage is False
    assert audit.reason == "source_label_maps_to_multiple_identifiers"
    assert audit.labels_with_multiple_identifiers == ("ranchi",)


def test_source_identifier_audit_rejects_many_to_many_ambiguity():
    audit = audit_source_identifier_pairs([
        ("101", "Ranchi"),
        ("101", "Khunti"),
        ("205", "Ranchi"),
    ])
    assert audit.safe_for_direct_linkage is False
    assert audit.reason == "many_to_many_source_identifier_label_ambiguity"


def test_source_identifier_audit_rejects_missing_identifiers_or_labels():
    audit = audit_source_identifier_pairs([
        ("101", "Ranchi"),
        ("", "Khunti"),
    ])
    assert audit.safe_for_direct_linkage is False
    assert audit.reason == "missing_source_identifier_or_label"


def test_source_identifier_audit_never_treats_clean_pairs_as_crosswalk_evidence():
    audit = audit_source_identifier_pairs([("101", "Ranchi")])
    assert audit.safe_for_direct_linkage is True
    assert "crosswalk_still_required" in audit.reason

    record = valid_record()
    record["source_code"] = "101"
    record["source_name"] = "Ranchi"
    record["target_name"] = "Ranchi"
    record.pop("evidence_url")
    assert validate_crosswalk_record(record).accepted is False
