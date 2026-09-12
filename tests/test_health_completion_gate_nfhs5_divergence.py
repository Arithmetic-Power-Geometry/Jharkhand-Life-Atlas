from pathlib import Path

import yaml


GATE = Path("modules/health_access/completion_gate.yaml")
EVIDENCE = Path(
    "modules/health_access/acquisition_evidence/"
    "2026-09-12_nfhs5_live_index_surface_divergence.yaml"
)


def _load(path: Path):
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def test_nfhs5_surface_divergence_is_formally_registered_without_publication():
    gate = _load(GATE)
    evidence = _load(EVIDENCE)

    registered = gate["verified_partial_evidence"][
        "nfhs5_live_index_surface_divergence_2026_09_12"
    ]

    assert gate["status"] == "open"
    assert registered["evidence"] == str(EVIDENCE)
    assert registered["status"] == evidence["interpretation"]["state"]
    assert registered["publication_allowed"] is False
    assert evidence["publication_allowed"] is False
    assert evidence["raw_payload_acquired"] is False
    assert evidence["raw_sha256"] is None


def test_nfhs5_divergence_registration_does_not_weaken_scientific_gates():
    gate = _load(GATE)
    criteria = gate["criteria"]

    for name in (
        "authoritative_acquisition",
        "smallest_authoritative_reusable_granularity",
        "cleaning_engineering",
        "geographic_linkage",
        "provenance",
        "indicators",
        "validation",
        "downloadable_data_reports",
    ):
        assert criteria[name]["satisfied"] is False, name

    assert "every criterion is satisfied" in gate["completion_rule"]
    assert "exact main head" in gate["completion_rule"]


def test_nfhs5_divergence_gate_preserves_null_and_no_name_equivalence_rules():
    gate = _load(GATE)
    registered = gate["verified_partial_evidence"][
        "nfhs5_live_index_surface_divergence_2026_09_12"
    ]
    rule = registered["rule"].lower()
    geography = gate["criteria"]["geographic_linkage"]["evidence"].lower()

    assert "null" in rule
    assert "publication closed" in rule
    assert "exact authoritative bytes" in rule
    assert "name equality alone is prohibited" in geography
