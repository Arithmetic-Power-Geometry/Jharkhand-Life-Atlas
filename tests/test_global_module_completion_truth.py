from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
MODULES = ROOT / "modules"


def _load(path: Path):
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(data, dict), f"{path} must contain a YAML mapping"
    return data


def _module_id(module: dict) -> str:
    value = module.get("id") or module.get("module")
    assert isinstance(value, str) and value.strip(), "module.yaml must declare id/module"
    return value.strip()


def test_every_completion_gate_agrees_with_module_status():
    """A gated module may never claim COMPLETE while any publication gate is open.

    This is deliberately repository-wide so newly added modules inherit the rule
    without needing a bespoke regression test. Modules that predate completion_gate.yaml
    retain their existing dedicated validators until migrated to the shared contract.
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

        assert gate.get("module") == module_id, (
            f"{module_dir.name}: completion gate belongs to {gate.get('module')!r}, "
            f"but module id is {module_id!r}"
        )

        criteria = gate.get("criteria")
        assert isinstance(criteria, dict) and criteria, (
            f"{module_dir.name}: completion gate must contain non-empty criteria"
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
        module_complete = str(module.get("status", "")).strip().lower() == "complete"

        # A gate may say complete only when every criterion is actually satisfied.
        if gate_complete:
            assert all_satisfied, (
                f"{module_dir.name}: gate status is complete but one or more criteria are open"
            )

        # The public module status may say complete only after the gate is complete.
        if module_complete:
            assert gate_complete and all_satisfied, (
                f"{module_dir.name}: module status is complete before its strict gate is complete"
            )

        # Conversely, a fully closed gate should not remain hidden behind a non-complete
        # public status; this prevents repository truth and Streamlit truth from drifting.
        if gate_complete and all_satisfied:
            assert module_complete, (
                f"{module_dir.name}: strict gate is complete but module status is not complete"
            )

    assert gated_modules > 0, "repository must contain at least one governed completion gate"
