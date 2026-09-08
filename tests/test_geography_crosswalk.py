from jla.geography_crosswalk import accepted_records, validate_crosswalk_record


def valid_record():
    return {
        "source_code": "C2011-001",
        "source_vintage": "Census-2011",
        "target_code": "LGD-001",
        "target_vintage": "LGD-2026-09-08",
        "relation": "same_unit",
        "evidence_url": "https://lgdirectory.gov.in/example-authoritative-record",
        "evidence_date": "2026-09-08",
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


def test_filter_never_promotes_invalid_records():
    good = valid_record()
    bad = valid_record()
    bad["target_code"] = "LGD-002"
    bad["evidence_url"] = "https://not-government.example/evidence"
    assert accepted_records([good, bad]) == [good]
