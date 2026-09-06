from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "modules" / "health_access" / "geography_crosswalk_schema.yaml"


def test_health_crosswalk_contract_is_fail_closed():
    schema = yaml.safe_load(CONTRACT.read_text(encoding="utf-8"))
    fields = schema["required_fields"]
    required = {
        "source_geography_vintage",
        "source_district_name",
        "source_district_code",
        "census2011_district_code",
        "relationship",
        "evidence_source_id",
        "evidence_url",
        "evidence_reference_date",
        "reviewed_on",
        "review_status",
        "notes",
    }
    assert set(fields) == required
    assert set(fields["relationship"]["values"]) == {
        "equivalent", "split", "merge", "boundary_change", "unresolved"
    }
    assert set(fields["review_status"]["values"]) == {
        "verified_equivalent", "non_equivalent", "unresolved"
    }
    gates = " ".join(schema["hard_gates"]).lower()
    assert "name equality alone" not in schema["publication_rule"].lower() or "no current" in schema["publication_rule"].lower()
    assert "relationship=equivalent" in gates
    assert "review_status=verified_equivalent" in gates
    assert "split" in gates and "merge" in gates and "boundary_change" in gates
    assert "publication aborts" in gates
    assert "must not be replaced" in gates
