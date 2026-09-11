import ast
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BUILDER = ROOT / "modules" / "health_access" / "build_census2011_health_extract.py"
DICTIONARY = ROOT / "modules" / "health_access" / "DATA_DICTIONARY_CENSUS2011.md"
PROVENANCE = ROOT / "data" / "curated" / "health_access" / "census_health_access_2011.provenance.json"


def _literal_assignment(path: Path, name: str):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == name:
                    return ast.literal_eval(node.value)
    raise AssertionError(f"{name} not found in {path}")


def test_health_dictionary_covers_governed_historical_fields_and_provenance():
    fields = _literal_assignment(BUILDER, "HEALTH_FIELDS")
    text = DICTIONARY.read_text(encoding="utf-8")
    provenance = json.loads(PROVENANCE.read_text(encoding="utf-8"))

    assert len(fields) == 69
    assert provenance["health_field_count"] == len(fields)
    assert provenance["row_count"] == 32394
    assert provenance["reference_year"] == 2011
    assert provenance["status"] == "validated_source_native_historical_extract"

    missing_from_dictionary = [field for field in fields if f"`{field}`" not in text]
    assert missing_from_dictionary == []

    assert provenance["source_sha256"] in text
    assert provenance["output_sha256"] in text
    assert "never converted to zero" in text
    assert "Census-2011 identifiers remain Census-2011 identifiers" in text
    assert "names alone are insufficient" in text
    assert "not a current facility inventory" in text
    assert "no person-level health records" in text
