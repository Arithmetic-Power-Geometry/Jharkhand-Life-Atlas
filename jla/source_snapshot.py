"""Validation helpers for authoritative source snapshots.

A source may be discovered without being acquired.  This module implements the
shared fail-closed checks defined by ``config/source_snapshot_contract.yaml`` so
module pipelines can make that distinction consistently.
"""

from __future__ import annotations

import re
from typing import Any, Mapping

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

_REQUIRED_SECTIONS = (
    "source_identity",
    "retrieval",
    "rights",
    "temporal_geographic_context",
    "observed_payload",
    "validation",
)

_REQUIRED_FIELDS = {
    "source_identity": (
        "module_id",
        "source_id",
        "source_title",
        "publisher",
        "authoritative_source_url",
        "exact_resource_or_api_url",
    ),
    "retrieval": (
        "retrieved_at_utc",
        "retrieval_method",
        "media_type",
        "byte_count",
        "sha256",
    ),
    "rights": (
        "publication_class",
        "licence_or_terms",
        "licence_url_or_terms_url",
        "rights_review_status",
        "attribution_requirement",
    ),
    "temporal_geographic_context": (
        "source_reference_period",
        "source_geography_vintage",
        "smallest_authoritative_reusable_granularity",
    ),
    "observed_payload": (
        "observed_schema",
        "record_count_before_jharkhand_filter",
        "jharkhand_filter_method",
        "record_count_after_jharkhand_filter",
        "source_record_identity_field_or_strategy",
        "null_semantics_reviewed",
    ),
    "validation": (
        "schema_validation_status",
        "geography_linkage_status",
        "provenance_validation_status",
        "module_tests_status",
    ),
}

_VERIFIED_STATUSES = {"verified", "passed", "pass", "complete", "approved"}


def _is_present(value: Any) -> bool:
    return value is not None and value != "" and value != [] and value != {}


def validate_source_snapshot(snapshot: Mapping[str, Any]) -> list[str]:
    """Return fail-closed validation errors for an acquired source snapshot.

    An empty error list means the manifest contains the minimum evidence needed
    to be treated as *acquired*.  It does not by itself make a module complete.
    """

    errors: list[str] = []

    for section in _REQUIRED_SECTIONS:
        payload = snapshot.get(section)
        if not isinstance(payload, Mapping):
            errors.append(f"missing section: {section}")
            continue
        for field in _REQUIRED_FIELDS[section]:
            if not _is_present(payload.get(field)):
                errors.append(f"missing field: {section}.{field}")

    retrieval = snapshot.get("retrieval") or {}
    byte_count = retrieval.get("byte_count")
    if byte_count is not None and (not isinstance(byte_count, int) or byte_count <= 0):
        errors.append("retrieval.byte_count must be a positive integer")
    sha256 = retrieval.get("sha256")
    if sha256 is not None and not _SHA256_RE.fullmatch(str(sha256).lower()):
        errors.append("retrieval.sha256 must be a 64-character SHA-256 hex digest")

    observed = snapshot.get("observed_payload") or {}
    before = observed.get("record_count_before_jharkhand_filter")
    after = observed.get("record_count_after_jharkhand_filter")
    for field, value in (("before", before), ("after", after)):
        if value is not None and (not isinstance(value, int) or value < 0):
            errors.append(f"observed_payload record count {field} must be a non-negative integer")
    if isinstance(before, int) and isinstance(after, int) and after > before:
        errors.append("Jharkhand-filtered record count cannot exceed source record count")
    if observed.get("null_semantics_reviewed") is not True:
        errors.append("observed_payload.null_semantics_reviewed must be true")
    schema = observed.get("observed_schema")
    if schema is not None and not isinstance(schema, (list, tuple, Mapping)):
        errors.append("observed_payload.observed_schema must be structured")

    rights = snapshot.get("rights") or {}
    if str(rights.get("rights_review_status", "")).lower() not in _VERIFIED_STATUSES:
        errors.append("rights.rights_review_status is not verified")

    validation = snapshot.get("validation") or {}
    for field in ("schema_validation_status", "provenance_validation_status", "module_tests_status"):
        value = str(validation.get(field, "")).lower()
        if value not in _VERIFIED_STATUSES:
            errors.append(f"validation.{field} is not verified")

    geography_status = str(validation.get("geography_linkage_status", "")).lower()
    if geography_status not in _VERIFIED_STATUSES and geography_status not in {
        "not_required",
        "not-required",
    }:
        errors.append("validation.geography_linkage_status is not verified")

    crosswalk = snapshot.get("temporal_crosswalk")
    if crosswalk is not None:
        if not isinstance(crosswalk, Mapping):
            errors.append("temporal_crosswalk must be structured")
        else:
            for field in ("crosswalk_source", "crosswalk_evidence_url", "relationship_type", "review_status"):
                if not _is_present(crosswalk.get(field)):
                    errors.append(f"missing field: temporal_crosswalk.{field}")
            relationship = str(crosswalk.get("relationship_type", "")).lower()
            review = str(crosswalk.get("review_status", "")).lower()
            if relationship == "equivalent" and review != "verified_equivalent":
                errors.append("equivalent temporal linkage requires verified_equivalent review")
            if relationship in {"split", "merge", "boundary_change", "unresolved"} and geography_status in _VERIFIED_STATUSES:
                errors.append("unresolved temporal relationship cannot be marked as verified direct geography linkage")

    if snapshot.get("missing_values_converted_to_zero") is True:
        errors.append("missing values must not be silently converted to zero")
    if snapshot.get("contains_sensitive_person_level_data") is True:
        errors.append("sensitive person-level data cannot satisfy the public snapshot contract")

    return errors


def source_snapshot_is_acquired(snapshot: Mapping[str, Any]) -> bool:
    """Return True only when all minimum acquisition checks pass."""

    return not validate_source_snapshot(snapshot)
