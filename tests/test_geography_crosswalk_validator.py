from modules.core_geography.crosswalk import publication_join_allowed, validate_crosswalk_record


def _verified_record():
    return {
        "source_system": "census",
        "source_vintage": "2011",
        "source_level": "village",
        "source_code": "SRC001",
        "target_system": "lgd",
        "target_vintage": "2026",
        "target_level": "village",
        "target_code": "TGT001",
        "relation": "same_entity",
        "evidence_type": "authoritative_code_crosswalk",
        "evidence_reference": "official:test-fixture",
        "review_status": "verified",
    }


def test_verified_evidence_backed_record_can_clear_publication_gate():
    record = _verified_record()
    assert validate_crosswalk_record(record, for_publication=True) == []
    assert publication_join_allowed(record) is True


def test_name_only_record_cannot_clear_publication_gate():
    record = _verified_record()
    record.pop("source_code")
    record["source_name"] = "Example Village"
    errors = validate_crosswalk_record(record, for_publication=True)
    assert "missing_required:source_code" in errors
    assert "code_required:source_code" in errors
    assert publication_join_allowed(record) is False


def test_provisional_record_cannot_clear_publication_gate():
    record = _verified_record()
    record["review_status"] = "provisional"
    assert "publication_requires_verified_record" in validate_crosswalk_record(record, for_publication=True)
    assert publication_join_allowed(record) is False


def test_verified_record_without_evidence_cannot_clear_publication_gate():
    record = _verified_record()
    record["evidence_reference"] = None
    errors = validate_crosswalk_record(record, for_publication=True)
    assert "verified_requires_evidence_reference" in errors
    assert "publication_requires_evidence_reference" in errors
    assert publication_join_allowed(record) is False


def test_unknown_relation_fails_closed():
    record = _verified_record()
    record["relation"] = "probably_same"
    assert "invalid_relation" in validate_crosswalk_record(record)
    assert publication_join_allowed(record) is False
