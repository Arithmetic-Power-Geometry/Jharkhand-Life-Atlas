"""Repository-truth service for Health publication readiness.

Scientific readiness is read from the governed tree. Exact-head CI is deliberately
supplied as post-commit external evidence so a commit is never required to contain
its own SHA.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
LEDGER_PATH = ROOT / "modules" / "health_access" / "publication_gates.json"
EXTERNAL_CI_GATE = "exact_final_main_green_ci"
EXPECTED_REPOSITORY = "Arithmetic-Power-Geometry/Jharkhand-Life-Atlas"
REQUIRED_WORKFLOWS = {"tests", "health-access-validation"}
_SHA40 = re.compile(r"^[0-9a-f]{40}$")


def health_publication_ledger() -> dict[str, Any]:
    return json.loads(LEDGER_PATH.read_text(encoding="utf-8"))


def verify_external_ci_attestation(attestation: dict[str, Any] | None, candidate_sha: str | None) -> bool:
    """Fail-closed verification of runtime, post-commit exact-head CI evidence."""
    if not attestation or not candidate_sha or not _SHA40.fullmatch(candidate_sha):
        return False
    if attestation.get("repository") != EXPECTED_REPOSITORY or attestation.get("head_sha") != candidate_sha:
        return False
    runs = attestation.get("workflow_runs")
    if not isinstance(runs, list):
        return False
    verified = set()
    for run in runs:
        if not isinstance(run, dict):
            continue
        name = run.get("name")
        url = str(run.get("url", ""))
        if (
            name in REQUIRED_WORKFLOWS
            and run.get("head_sha") == candidate_sha
            and run.get("conclusion") == "success"
            and url.startswith(f"https://github.com/{EXPECTED_REPOSITORY}/actions/runs/")
        ):
            verified.add(name)
    return verified == REQUIRED_WORKFLOWS


def health_publication_status(
    *, candidate_sha: str | None = None, external_ci_attestation: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Return fail-closed Health readiness, separating tree gates from external CI."""
    ledger = health_publication_ledger()
    gates = ledger.get("gates", {})
    scientific_gates = {k: v for k, v in gates.items() if k != EXTERNAL_CI_GATE}
    scientific_unresolved = [k for k, v in scientific_gates.items() if v.get("satisfied") is not True]
    candidate_ready = bool(scientific_gates) and not scientific_unresolved
    external_ci_verified = verify_external_ci_attestation(external_ci_attestation, candidate_sha)

    effective = {k: dict(v) for k, v in gates.items()}
    if EXTERNAL_CI_GATE in effective:
        effective[EXTERNAL_CI_GATE]["tree_satisfied"] = effective[EXTERNAL_CI_GATE].get("satisfied") is True
        effective[EXTERNAL_CI_GATE]["satisfied"] = external_ci_verified
        effective[EXTERNAL_CI_GATE]["runtime_verified"] = external_ci_verified
    satisfied = [k for k, v in effective.items() if v.get("satisfied") is True]
    unresolved = [k for k, v in effective.items() if v.get("satisfied") is not True]

    publication_allowed = ledger.get("publication_allowed") is True and candidate_ready and external_ci_verified
    module_complete = ledger.get("module_complete") is True and publication_allowed
    return {
        "status": "COMPLETE" if module_complete else str(ledger.get("status", "IN DEVELOPMENT")),
        "publication_allowed": publication_allowed,
        "module_complete": module_complete,
        "candidate_ready": candidate_ready,
        "external_ci_verified": external_ci_verified,
        "gate_count": len(gates),
        "satisfied_count": len(satisfied),
        "unresolved_count": len(unresolved),
        "satisfied_gates": satisfied,
        "unresolved_gates": unresolved,
        "scientific_unresolved_gates": scientific_unresolved,
        "gates": effective,
    }
