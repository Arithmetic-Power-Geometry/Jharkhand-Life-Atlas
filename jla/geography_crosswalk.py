"""Fail-closed geography crosswalk validation for JLA.

This module validates *evidence-backed* administrative-unit equivalence across
vintages. It deliberately does not perform fuzzy/name matching and cannot create
crosswalks from names alone.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping
from urllib.parse import urlparse


ALLOWED_RELATIONS = {
    "same_unit",
    "split_from",
    "merged_into",
    "renamed_with_authoritative_evidence",
    "boundary_changed",
}


@dataclass(frozen=True)
class CrosswalkDecision:
    accepted: bool
    reason: str


def _nonempty(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _authoritative_url(value: object) -> bool:
    if not _nonempty(value):
        return False
    parsed = urlparse(str(value).strip())
    if parsed.scheme != "https" or not parsed.hostname:
        return False
    host = parsed.hostname.lower()
    return host == "gov.in" or host.endswith(".gov.in") or host == "nic.in" or host.endswith(".nic.in")


def validate_crosswalk_record(record: Mapping[str, object]) -> CrosswalkDecision:
    """Validate one cross-vintage equivalence/relationship record.

    Required safeguards:
    - source/target codes and vintages must be explicit;
    - names may be retained for display but cannot establish equivalence;
    - relation must be controlled;
    - an authoritative government evidence URL and evidence date are mandatory;
    - same-unit claims require an explicit evidence statement, not merely equal names.
    """

    required = ("source_code", "source_vintage", "target_code", "target_vintage", "relation")
    missing = [key for key in required if not _nonempty(record.get(key))]
    if missing:
        return CrosswalkDecision(False, f"missing_required:{','.join(missing)}")

    if record.get("relation") not in ALLOWED_RELATIONS:
        return CrosswalkDecision(False, "unsupported_relation")

    if str(record["source_vintage"]).strip() == str(record["target_vintage"]).strip():
        return CrosswalkDecision(False, "crosswalk_requires_distinct_vintages")

    if not _authoritative_url(record.get("evidence_url")):
        return CrosswalkDecision(False, "authoritative_evidence_url_required")

    if not _nonempty(record.get("evidence_date")):
        return CrosswalkDecision(False, "evidence_date_required")

    if not _nonempty(record.get("evidence_statement")):
        return CrosswalkDecision(False, "evidence_statement_required")

    if record.get("relation") == "same_unit" and not _nonempty(record.get("evidence_reference_id")):
        return CrosswalkDecision(False, "same_unit_requires_evidence_reference_id")

    return CrosswalkDecision(True, "accepted")


def validate_crosswalk(records: Iterable[Mapping[str, object]]) -> list[CrosswalkDecision]:
    """Validate records independently; never infer missing mappings."""

    return [validate_crosswalk_record(record) for record in records]


def accepted_records(records: Iterable[Mapping[str, object]]) -> list[Mapping[str, object]]:
    """Return only records that pass the strict evidence gate."""

    output: list[Mapping[str, object]] = []
    for record in records:
        if validate_crosswalk_record(record).accepted:
            output.append(record)
    return output
