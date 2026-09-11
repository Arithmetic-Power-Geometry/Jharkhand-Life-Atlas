from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RESOLVER = ROOT / "modules" / "health_access" / "resolve_ogd_hospital_resource_identity.py"
WORKFLOW = ROOT / ".github" / "workflows" / "health-ogd-resource-identity.yml"


def _resolver_contract() -> str:
    text = RESOLVER.read_text(encoding="utf-8")
    match = re.search(r'"contract"\s*:\s*"([A-Z0-9_]+)"', text)
    assert match, "Health OGD identity resolver contract declaration not found"
    return match.group(1)


def _workflow_contract() -> str:
    text = WORKFLOW.read_text(encoding="utf-8")
    match = re.search(r"r\['contract'\]\s*==\s*'([A-Z0-9_]+)'", text)
    assert match, "Health OGD identity workflow contract assertion not found"
    return match.group(1)


def test_health_ogd_identity_workflow_tracks_resolver_contract() -> None:
    assert _resolver_contract() == _workflow_contract()


def test_health_ogd_identity_workflow_keeps_fail_closed_guards() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    required = [
        "never_construct_resource_uuid_from_title_or_slug",
        "never_construct_download_url_from_title_or_slug",
        "structured_json_candidates_require_target_and_explicit_identity_in_same_object",
        "identity_resolution_does_not_mean_payload_acquisition_or_publication",
        "publication_allowed'] is False",
        "raw_payload_acquired'] is False",
        "schema_inspected'] is False",
    ]
    missing = [rule for rule in required if rule not in text]
    assert not missing, f"Health OGD identity workflow lost fail-closed guards: {missing}"
