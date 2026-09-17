"""Fail-closed validation for evidence-backed cross-vintage geography links."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

CONTRACT_PATH = Path(__file__).with_name("geography_crosswalk_contract.json")


def load_contract(path: Path = CONTRACT_PATH) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_crosswalk_record(record: Mapping[str, Any], *, for_publication: bool = False) -> list[str]:
    """Return validation errors; an empty list means the record satisfies the contract.

    Publication use is stricter: only verified, evidence-backed records may pass.
    No name-based fallback is implemented by design.
    """
    contract = load_contract()
    errors: list[str] = []

    for field in contract["required_fields"]:
        value = record.get(field)
        if value is None or (isinstance(value, str) and not value.strip()):
            errors.append(f"missing_required:{field}")

    relation = record.get("relation")
    if relation is not None and relation not in contract["allowed_relations"]:
        errors.append("invalid_relation")

    review_status = record.get("review_status")
    if review_status is not None and review_status not in contract["allowed_review_status"]:
        errors.append("invalid_review_status")

    # Codes are mandatory for an asserted cross-vintage relationship. A name is
    # never accepted as a substitute for an absent code.
    for field in ("source_code", "target_code"):
        value = record.get(field)
        if value is None or (isinstance(value, str) and not value.strip()):
            marker = f"code_required:{field}"
            if marker not in errors:
                errors.append(marker)

    if review_status == "verified":
        evidence = record.get("evidence_reference")
        if evidence is None or (isinstance(evidence, str) and not evidence.strip()):
            errors.append("verified_requires_evidence_reference")

    if for_publication:
        if review_status != "verified":
            errors.append("publication_requires_verified_record")
        evidence = record.get("evidence_reference")
        if evidence is None or (isinstance(evidence, str) and not evidence.strip()):
            errors.append("publication_requires_evidence_reference")

    return sorted(set(errors))


def publication_join_allowed(record: Mapping[str, Any]) -> bool:
    """True only for a contract-valid record explicitly cleared for publication."""
    return not validate_crosswalk_record(record, for_publication=True)
