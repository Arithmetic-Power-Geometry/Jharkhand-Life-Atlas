"""Fail-closed geography crosswalk validation for JLA.

This module validates *evidence-backed* administrative-unit equivalence across
vintages. It deliberately does not perform fuzzy/name matching and cannot create
crosswalks from names alone. Cross-vintage claims must also carry an immutable
SHA-256 fingerprint for the exact authoritative evidence snapshot used.

It also provides a source-identifier ambiguity audit for thematic datasets. That
audit may prove that a source's own identifier/name pairs are unsafe for direct
linkage, but it can never promote name equality into an administrative crosswalk.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import re
from typing import Iterable, Mapping
from urllib.parse import urlparse


ALLOWED_RELATIONS = {
    "same_unit",
    "split_from",
    "merged_into",
    "renamed_with_authoritative_evidence",
    "boundary_changed",
}

_SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")
_NON_ALNUM_RE = re.compile(r"[^a-z0-9]+")


@dataclass(frozen=True)
class CrosswalkDecision:
    accepted: bool
    reason: str


@dataclass(frozen=True)
class SourceIdentifierAudit:
    """Diagnostic result for identifiers embedded in an external source.

    ``safe_for_direct_linkage`` only means that the observed source ID/label
    relation is internally one-to-one. It does *not* establish equivalence with
    LGD, Census, or any other administrative vintage.
    """

    safe_for_direct_linkage: bool
    reason: str
    observed_pair_count: int
    distinct_identifier_count: int
    distinct_label_count: int
    identifiers_with_multiple_labels: tuple[str, ...]
    labels_with_multiple_identifiers: tuple[str, ...]


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


def _iso_date(value: object) -> bool:
    if not _nonempty(value):
        return False
    raw = str(value).strip()
    if len(raw) != 10:
        return False
    try:
        parsed = date.fromisoformat(raw)
    except ValueError:
        return False
    return parsed.isoformat() == raw


def _sha256(value: object) -> bool:
    return _nonempty(value) and bool(_SHA256_RE.fullmatch(str(value).strip()))


def _diagnostic_label(value: object) -> str:
    """Normalize only for ambiguity detection, never for equivalence creation."""

    if not _nonempty(value):
        return ""
    return _NON_ALNUM_RE.sub(" ", str(value).casefold()).strip()


def audit_source_identifier_pairs(
    pairs: Iterable[tuple[object, object]],
) -> SourceIdentifierAudit:
    """Fail closed when a source's own identifier/label relation is ambiguous.

    This is a diagnostic gate for source ingestion. Empty identifiers or labels,
    one identifier observed with multiple normalized labels, or one normalized
    label observed with multiple identifiers all make direct source-ID linkage
    unsafe. A clean result still does not authorize mapping to another geography
    system; that requires :func:`validate_crosswalk_record` evidence.
    """

    identifier_to_labels: dict[str, set[str]] = {}
    label_to_identifiers: dict[str, set[str]] = {}
    observed_pair_count = 0
    invalid_pair_seen = False

    for raw_identifier, raw_label in pairs:
        observed_pair_count += 1
        if not _nonempty(raw_identifier) or not _nonempty(raw_label):
            invalid_pair_seen = True
            continue

        identifier = str(raw_identifier).strip()
        label = _diagnostic_label(raw_label)
        if not label:
            invalid_pair_seen = True
            continue

        identifier_to_labels.setdefault(identifier, set()).add(label)
        label_to_identifiers.setdefault(label, set()).add(identifier)

    identifiers_with_multiple_labels = tuple(
        sorted(identifier for identifier, labels in identifier_to_labels.items() if len(labels) > 1)
    )
    labels_with_multiple_identifiers = tuple(
        sorted(label for label, identifiers in label_to_identifiers.items() if len(identifiers) > 1)
    )

    if observed_pair_count == 0:
        reason = "no_observed_identifier_label_pairs"
        safe = False
    elif invalid_pair_seen:
        reason = "missing_source_identifier_or_label"
        safe = False
    elif identifiers_with_multiple_labels and labels_with_multiple_identifiers:
        reason = "many_to_many_source_identifier_label_ambiguity"
        safe = False
    elif identifiers_with_multiple_labels:
        reason = "source_identifier_maps_to_multiple_labels"
        safe = False
    elif labels_with_multiple_identifiers:
        reason = "source_label_maps_to_multiple_identifiers"
        safe = False
    else:
        reason = "internally_one_to_one_only_crosswalk_still_required"
        safe = True

    return SourceIdentifierAudit(
        safe_for_direct_linkage=safe,
        reason=reason,
        observed_pair_count=observed_pair_count,
        distinct_identifier_count=len(identifier_to_labels),
        distinct_label_count=len(label_to_identifiers),
        identifiers_with_multiple_labels=identifiers_with_multiple_labels,
        labels_with_multiple_identifiers=labels_with_multiple_identifiers,
    )


def validate_crosswalk_record(record: Mapping[str, object]) -> CrosswalkDecision:
    """Validate one cross-vintage equivalence/relationship record.

    Required safeguards:
    - source/target codes and vintages must be explicit;
    - names may be retained for display but cannot establish equivalence;
    - relation must be controlled;
    - an authoritative government evidence URL is mandatory;
    - evidence date must be a real ISO calendar date (YYYY-MM-DD);
    - the exact evidence snapshot must have a SHA-256 fingerprint;
    - same-unit claims require an explicit evidence reference, not merely equal names.
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

    if not _iso_date(record.get("evidence_date")):
        return CrosswalkDecision(False, "evidence_date_must_be_iso_calendar_date")

    if not _sha256(record.get("evidence_sha256")):
        return CrosswalkDecision(False, "evidence_sha256_required")

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
