import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "modules" / "health_access" / "publication_gates.json"


def _ledger():
    return json.loads(LEDGER.read_text(encoding="utf-8"))


def test_health_publication_gate_ledger_is_fail_closed():
    ledger = _ledger()
    assert ledger["module"] == "health_access"
    assert ledger["status"] in {"COMPLETE", "IN DEVELOPMENT", "PLANNED"}
    assert isinstance(ledger["publication_allowed"], bool)
    assert isinstance(ledger["module_complete"], bool)
    assert ledger["gates"]

    for name, gate in ledger["gates"].items():
        assert isinstance(gate.get("satisfied"), bool), name
        if not gate["satisfied"]:
            assert str(gate.get("reason", "")).strip(), name

    all_satisfied = all(gate["satisfied"] for gate in ledger["gates"].values())
    if ledger["module_complete"] or ledger["publication_allowed"]:
        assert all_satisfied
        assert ledger["module_complete"] is True
        assert ledger["publication_allowed"] is True
        assert ledger["status"] == "COMPLETE"
    else:
        assert ledger["status"] != "COMPLETE"


def test_satisfied_health_gates_reference_repository_evidence():
    ledger = _ledger()
    for name, gate in ledger["gates"].items():
        if not gate["satisfied"]:
            continue
        evidence = gate.get("evidence")
        assert isinstance(evidence, list) and evidence, name
        for relative_path in evidence:
            path = ROOT / relative_path
            assert path.exists(), f"{name}: missing evidence {relative_path}"
            assert path.is_file(), f"{name}: evidence is not a file {relative_path}"


def test_current_health_ledger_does_not_overclaim_completion():
    ledger = _ledger()
    unsatisfied = {
        name for name, gate in ledger["gates"].items() if not gate["satisfied"]
    }
    if unsatisfied:
        assert ledger["module_complete"] is False
        assert ledger["publication_allowed"] is False
        assert ledger["status"] == "IN DEVELOPMENT"
