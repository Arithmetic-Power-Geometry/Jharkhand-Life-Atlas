"""Repository-truth service for Health publication readiness.

This module deliberately reads the governed publication-gate ledger rather than
reconstructing readiness from UI counters, acquisition success, or green CI.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
LEDGER_PATH = ROOT / "modules" / "health_access" / "publication_gates.json"


def health_publication_ledger() -> dict[str, Any]:
    """Return the governed Health publication ledger."""
    return json.loads(LEDGER_PATH.read_text(encoding="utf-8"))


def health_publication_status() -> dict[str, Any]:
    """Return a compact, fail-closed status derived only from the ledger."""
    ledger = health_publication_ledger()
    gates = ledger.get("gates", {})
    satisfied = [name for name, gate in gates.items() if gate.get("satisfied") is True]
    unresolved = [name for name, gate in gates.items() if gate.get("satisfied") is not True]
    all_satisfied = bool(gates) and not unresolved

    # Never infer completion from acquisition counters or CI alone.  The ledger
    # must explicitly authorize publication and every governed gate must pass.
    publication_allowed = ledger.get("publication_allowed") is True and all_satisfied
    module_complete = ledger.get("module_complete") is True and publication_allowed

    return {
        "status": "COMPLETE" if module_complete else str(ledger.get("status", "IN DEVELOPMENT")),
        "publication_allowed": publication_allowed,
        "module_complete": module_complete,
        "gate_count": len(gates),
        "satisfied_count": len(satisfied),
        "unresolved_count": len(unresolved),
        "satisfied_gates": satisfied,
        "unresolved_gates": unresolved,
        "gates": gates,
    }
