"""Build reproducible evidence receipts for locally acquired public source payloads.

This helper deliberately does not download data and does not transform source values.
It records immutable byte identity, observed schema, source row counts, and an explicit
Jharkhand filter count so an acquisition can later be reviewed under the shared
source-snapshot contract.
"""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
from typing import Any


def _normalise_text(value: Any) -> str:
    return " ".join(str(value).strip().casefold().split())


def _read_csv(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError("CSV payload has no header")
        return list(reader), list(reader.fieldnames)


def _read_json(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    with path.open("r", encoding="utf-8-sig") as handle:
        payload = json.load(handle)
    if isinstance(payload, dict) and isinstance(payload.get("records"), list):
        payload = payload["records"]
    if not isinstance(payload, list):
        raise ValueError("JSON payload must be a list or an object containing a records list")
    if any(not isinstance(row, dict) for row in payload):
        raise ValueError("JSON records must be objects")
    rows: list[dict[str, Any]] = payload
    fields: list[str] = []
    seen: set[str] = set()
    for row in rows:
        for key in row:
            if key not in seen:
                seen.add(key)
                fields.append(key)
    return rows, fields


def build_acquisition_receipt(path: str | Path, *, state_field: str, state_value: str = "Jharkhand") -> dict[str, Any]:
    """Return immutable acquisition evidence without transforming source values."""
    source_path = Path(path)
    raw = source_path.read_bytes()
    if not raw:
        raise ValueError("source payload is empty")
    suffix = source_path.suffix.casefold()
    if suffix == ".csv":
        rows, fields = _read_csv(source_path)
        media_type = "text/csv"
    elif suffix == ".json":
        rows, fields = _read_json(source_path)
        media_type = "application/json"
    else:
        raise ValueError("only CSV and JSON payloads are supported")
    if state_field not in fields:
        raise ValueError(f"state field not found in observed schema: {state_field}")
    target = _normalise_text(state_value)
    filtered_count = sum(_normalise_text(row.get(state_field, "")) == target for row in rows)
    return {
        "retrieval": {"media_type": media_type, "byte_count": len(raw), "sha256": hashlib.sha256(raw).hexdigest()},
        "observed_payload": {
            "observed_schema": fields,
            "record_count_before_jharkhand_filter": len(rows),
            "jharkhand_filter_method": f"exact case/whitespace-normalised equality on source field {state_field!r} to {state_value!r}",
            "record_count_after_jharkhand_filter": filtered_count,
            "null_semantics_reviewed": False,
        },
    }


def build_source_snapshot_draft(
    path: str | Path,
    *, module_id: str, source_id: str, source_title: str, publisher: str,
    authoritative_source_url: str, exact_resource_or_api_url: str,
    retrieved_at_utc: str, retrieval_method: str, publication_class: str,
    licence_or_terms: str, licence_url_or_terms_url: str, attribution_requirement: str,
    source_reference_period: str, source_geography_vintage: str,
    smallest_authoritative_reusable_granularity: str,
    source_record_identity_field_or_strategy: str, state_field: str,
    state_value: str = "Jharkhand",
) -> dict[str, Any]:
    """Build a fail-closed JLA_SOURCE_SNAPSHOT_V1 draft around observed payload facts.

    Review-dependent fields deliberately remain pending, so this draft cannot itself
    satisfy the acquired-source gate.
    """
    receipt = build_acquisition_receipt(path, state_field=state_field, state_value=state_value)
    receipt["retrieval"].update({"retrieved_at_utc": retrieved_at_utc, "retrieval_method": retrieval_method})
    receipt["observed_payload"]["source_record_identity_field_or_strategy"] = source_record_identity_field_or_strategy
    return {
        "contract": "JLA_SOURCE_SNAPSHOT_V1",
        "source_identity": {
            "module_id": module_id, "source_id": source_id, "source_title": source_title,
            "publisher": publisher, "authoritative_source_url": authoritative_source_url,
            "exact_resource_or_api_url": exact_resource_or_api_url,
        },
        "retrieval": receipt["retrieval"],
        "rights": {
            "publication_class": publication_class, "licence_or_terms": licence_or_terms,
            "licence_url_or_terms_url": licence_url_or_terms_url,
            "rights_review_status": "pending_review", "attribution_requirement": attribution_requirement,
        },
        "temporal_geographic_context": {
            "source_reference_period": source_reference_period,
            "source_geography_vintage": source_geography_vintage,
            "smallest_authoritative_reusable_granularity": smallest_authoritative_reusable_granularity,
        },
        "observed_payload": receipt["observed_payload"],
        "validation": {
            "schema_validation_status": "pending_review", "geography_linkage_status": "pending_review",
            "provenance_validation_status": "pending_review", "module_tests_status": "pending_review",
        },
        "missing_values_converted_to_zero": False,
        "contains_sensitive_person_level_data": False,
    }
