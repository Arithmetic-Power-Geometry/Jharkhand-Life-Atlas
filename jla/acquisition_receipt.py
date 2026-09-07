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
from typing import Any, Iterable


def _normalise_text(value: Any) -> str:
    return " ".join(str(value).strip().casefold().split())


def _read_csv(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError("CSV payload has no header")
        rows = list(reader)
        return rows, list(reader.fieldnames)


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


def build_acquisition_receipt(
    path: str | Path,
    *,
    state_field: str,
    state_value: str = "Jharkhand",
) -> dict[str, Any]:
    """Return immutable acquisition evidence for a CSV or JSON payload.

    The function performs no filling, coercion, aggregation, or missing-to-zero
    conversion. The Jharkhand count is based only on an explicitly supplied source
    field and an exact whitespace/case-normalised equality test.
    """

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
        "retrieval": {
            "media_type": media_type,
            "byte_count": len(raw),
            "sha256": hashlib.sha256(raw).hexdigest(),
        },
        "observed_payload": {
            "observed_schema": fields,
            "record_count_before_jharkhand_filter": len(rows),
            "jharkhand_filter_method": (
                f"exact case/whitespace-normalised equality on source field {state_field!r} "
                f"to {state_value!r}"
            ),
            "record_count_after_jharkhand_filter": filtered_count,
            "null_semantics_reviewed": False,
        },
    }
