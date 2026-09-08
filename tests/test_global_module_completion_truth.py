from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
MODULES = ROOT / "modules"


def _load(path: Path):
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict), f"{path} must contain a YAML mapping"
    return data


def _module_id(module: dict) -> str:
    value = module.get("id") or module.get("module") or module.get("module_id")
    assert isinstance(value, str) and value.strip(), "module.yaml must declare id/module/module_id"
    return value.strip()


def _gate_module_id(gate: dict) -> str:
    value = gate.get("module") or gate.get("module_id")
    assert isinstance(value, str) and value.strip(), (
        "completion_gate.yaml must declare module or module_id"
    )
    return value.strip()


def _gate_truth(module_dir: Path, gate: dict) -> tuple[bool, bool]:
    """Return (gate_complete, all_satisfied) for either governed gate schema.

    Newer gates use criteria.<name>.satisfied with explicit evidence. Earlier gates
    use publication_gate.<name>: bool plus complete: bool. Both are fail-closed and
    remain supported until the earlier modules are migrated deliberately.
    """
    criteria = gate.get("criteria")
    if criteria is not None:
        assert isinstance(criteria, dict) and criteria, (
            f"{module_dir.name}: completion gate criteria must be a non-empty mapping"
        )
        for name, item in criteria.items():
            assert isinstance(item, dict), f"{module_dir.name}:{name} must be a mapping"
            assert isinstance(item.get("satisfied"), bool), (
                f"{module_dir.name}:{name}.satisfied must be boolean"
            )
            evidence = item.get("evidence")
            assert isinstance(evidence, str) and evidence.strip(), (
                f"{module_dir.name}:{name} must carry explicit evidence"
            )
        all_satisfied = all(item["satisfied"] for item in criteria.values())
        gate_complete = str(gate.get("status", "")).strip().lower() == "complete"
        return gate_complete, all_satisfied

    publication_gate = gate.get("publication_gate")
    assert isinstance(publication_gate, dict) and publication_gate, (
        f"{module_dir.name}: completion gate must contain criteria or publication_gate"
    )
    for name, value in publication_gate.items():
        assert isinstance(value, bool), (
            f"{module_dir.name}:publication_gate.{name} must be boolean"
        )

    all_satisfied = all(publication_gate.values())
    complete_value = gate.get("complete")
    assert isinstance(complete_value, bool), (
        f"{module_dir.name}: legacy completion gate must declare boolean complete"
    )
    status_complete = str(gate.get("status", "")).strip().lower() == "complete"
    # Either field may express completion, but contradictory completion truth is invalid.
    assert complete_value == status_complete, (
        f"{module_dir.name}: completion gate complete/status fields disagree"
    )
    return complete_value, all_satisfied


def test_every_completion_gate_agrees_with_module_status():
    """A gated module may never claim COMPLETE while any publication gate is open.

    This is deliberately repository-wide so newly added modules inherit the rule.
    Both the explicit-evidence criteria schema and the earlier boolean publication_gate
    schema are supported without weakening either contract.
    """
    gated_modules = 0

    for module_dir in sorted(path for path in MODULES.iterdir() if path.is_dir()):
        module_path = module_dir / "module.yaml"
        gate_path = module_dir / "completion_gate.yaml"
        if not module_path.exists() or not gate_path.exists():
            continue

        gated_modules += 1
        module = _load(module_path)
        gate = _load(gate_path)
        module_id = _module_id(module)
        gate_module_id = _gate_module_id(gate)

        assert gate_module_id == module_id, (
            f"{module_dir.name}: completion gate belongs to {gate_module_id!r}, "
            f"but module id is {module_id!r}"
        )

        gate_complete, all_satisfied = _gate_truth(module_dir, gate)
        module_complete = str(module.get("status", "")).strip().lower() == "complete"

        if gate_complete:
            assert all_satisfied, (
                f"{module_dir.name}: gate is complete but one or more criteria are open"
            )

        if module_complete:
            assert gate_complete and all_satisfied, (
                f"{module_dir.name}: module status is complete before its strict gate is complete"
            )

        if gate_complete and all_satisfied:
            assert module_complete, (
                f"{module_dir.name}: strict gate is complete but module status is not complete"
            )

    assert gated_modules > 0, "repository must contain at least one governed completion gate"
