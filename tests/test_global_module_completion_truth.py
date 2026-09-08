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
    """Return (gate_complete, all_satisfied) for every governed gate schema.

    Supported schemas are intentionally fail-closed:
    * criteria.<name>.satisfied with explicit evidence;
    * publication_gate.<name>: bool plus complete: bool;
    * requirements.<name>.passed plus publication_ready: bool.

    A schema is accepted only when its required booleans are explicit. This preserves
    the repository-wide completion invariant while older modules are migrated deliberately.
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
    if publication_gate is not None:
        assert isinstance(publication_gate, dict) and publication_gate, (
            f"{module_dir.name}: publication_gate must be a non-empty mapping"
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
        assert complete_value == status_complete, (
            f"{module_dir.name}: completion gate complete/status fields disagree"
        )
        return complete_value, all_satisfied

    requirements = gate.get("requirements")
    assert isinstance(requirements, dict) and requirements, (
        f"{module_dir.name}: completion gate must contain criteria, publication_gate, or requirements"
    )
    for name, item in requirements.items():
        assert isinstance(item, dict), f"{module_dir.name}:requirements.{name} must be a mapping"
        assert isinstance(item.get("passed"), bool), (
            f"{module_dir.name}:requirements.{name}.passed must be boolean"
        )
        rule = item.get("rule")
        assert isinstance(rule, str) and rule.strip(), (
            f"{module_dir.name}:requirements.{name} must carry an explicit rule"
        )

    all_satisfied = all(item["passed"] for item in requirements.values())
    publication_ready = gate.get("publication_ready")
    assert isinstance(publication_ready, bool), (
        f"{module_dir.name}: requirements gate must declare boolean publication_ready"
    )
    status_complete = str(gate.get("status", "")).strip().lower() == "complete"
    assert publication_ready == status_complete, (
        f"{module_dir.name}: publication_ready/status fields disagree"
    )
    return publication_ready, all_satisfied


def test_every_completion_gate_agrees_with_module_status():
    """A gated module may never claim COMPLETE while any publication gate is open.

    This is deliberately repository-wide so newly added modules inherit the rule.
    Explicit-evidence criteria, boolean publication gates, and requirement/pass gates
    are all supported without weakening their contracts.
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
