from __future__ import annotations

import ast
import csv
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
HEALTH = ROOT / "modules" / "health_access"


def _canonical_source_ids() -> set[str]:
    payload = yaml.safe_load((HEALTH / "sources.yaml").read_text(encoding="utf-8"))
    return {row["source_id"] for row in payload["sources"]}


def _coverage_source_ids() -> set[str]:
    with (HEALTH / "source_coverage.csv").open(encoding="utf-8", newline="") as handle:
        return {row["source_id"] for row in csv.DictReader(handle)}


def _literal_assignment(path: Path, name: str) -> str:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == name:
                    value = ast.literal_eval(node.value)
                    assert isinstance(value, str)
                    return value
    raise AssertionError(f"{name} is not a literal assignment in {path}")


def test_every_health_evidence_coverage_source_is_canonically_registered() -> None:
    canonical = _canonical_source_ids()
    coverage = _coverage_source_ids()
    missing = sorted(coverage - canonical)
    assert not missing, f"Health source_coverage.csv contains unregistered sources: {missing}"


def test_pakur_hmis_acquisition_target_matches_canonical_registry() -> None:
    script = HEALTH / "acquire_ogd_hmis_pakur_2019_20_november.py"
    source_id = _literal_assignment(script, "SOURCE_ID")
    resource_page = _literal_assignment(script, "RESOURCE_PAGE")

    payload = yaml.safe_load((HEALTH / "sources.yaml").read_text(encoding="utf-8"))
    entries = {row["source_id"]: row for row in payload["sources"]}

    assert source_id in entries
    assert entries[source_id]["url"] == resource_page
    assert entries[source_id]["acquisition_status"] == "governed_acquisition_active_payload_not_yet_admitted"
    assert entries[source_id]["data_api_status"] == "unavailable_on_live_resource_page"
    assert entries[source_id]["publication_class"] == "OPEN_WITH_ATTRIBUTION"
    assert "ogdl" in entries[source_id]["license_review_status"].casefold()
