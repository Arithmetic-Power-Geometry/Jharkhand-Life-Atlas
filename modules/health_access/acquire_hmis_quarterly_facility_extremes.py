#!/usr/bin/env python3
"""Fail-closed acquisition probe for the official OGD quarterly HMIS facility-extremes catalog.

This script is intentionally conservative. It snapshots only bytes returned by the exact
authoritative OGD control URL already pinned in sources.yaml, records SHA-256 and observed
response metadata, and never promotes those bytes to a curated/public dataset. If the
endpoint exposes structured JSON, a shallow schema/key inventory is recorded for later
resource-level resolution. No facility ranking, Jharkhand membership, geography linkage,
or completeness claim is inferred from catalog metadata.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

SOURCE_ID = "OGD_HMIS_QUARTERLY_FACILITY_EXTREMES_2026"
CATALOG_ID = "efc4b11e-30ca-4e02-a168-902d34c2e7a0"
AUTHORITY = "Ministry of Health and Family Welfare, Department of Health and Family Welfare, Government of India"
CATALOG_PAGE = "https://www.data.gov.in/catalog/all-india-level-quarterly-maximum-and-minimum-performing-public-health-facilities-selected"
CONTROL_URL = f"https://www.data.gov.in/apis/{CATALOG_ID}"


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def json_shape(value: Any, depth: int = 0) -> Any:
    """Return a bounded structural inventory without copying record values."""
    if depth >= 4:
        return type(value).__name__
    if isinstance(value, dict):
        return {str(k): json_shape(v, depth + 1) for k, v in list(value.items())[:80]}
    if isinstance(value, list):
        if not value:
            return []
        return [json_shape(value[0], depth + 1)]
    return type(value).__name__


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--timeout", type=float, default=45.0)
    args = parser.parse_args()

    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    observed_at = datetime.now(timezone.utc).isoformat()

    receipt = {
        "contract": "JLA_SOURCE_PROBE_V1",
        "source_id": SOURCE_ID,
        "authority": AUTHORITY,
        "catalog_id": CATALOG_ID,
        "catalog_page": CATALOG_PAGE,
        "control_url": CONTROL_URL,
        "observed_at_utc": observed_at,
        "publication_allowed": False,
        "curated_output_created": False,
        "jharkhand_membership_inferred": False,
        "facility_completeness_inferred": False,
        "direct_geography_equivalence_allowed": False,
        "missing_values_may_be_converted_to_zero": False,
    }

    try:
        response = requests.get(
            CONTROL_URL,
            timeout=args.timeout,
            headers={"User-Agent": "Jharkhand-Life-Atlas/health-authoritative-acquisition"},
        )
        receipt["http_status"] = response.status_code
        receipt["content_type"] = response.headers.get("content-type")
        response.raise_for_status()
        payload = response.content
        if not payload:
            raise RuntimeError("authoritative control returned zero bytes")

        raw_path = out / "official_catalog_api_response.bin"
        raw_path.write_bytes(payload)
        receipt.update(
            {
                "raw_control_response_acquired": True,
                "byte_count": len(payload),
                "sha256": sha256_bytes(payload),
                "raw_snapshot": raw_path.name,
            }
        )

        try:
            structured = response.json()
        except ValueError:
            receipt["structured_json_observed"] = False
        else:
            receipt["structured_json_observed"] = True
            receipt["observed_json_shape"] = json_shape(structured)
            (out / "observed_json_shape.json").write_text(
                json.dumps(receipt["observed_json_shape"], indent=2, sort_keys=True),
                encoding="utf-8",
            )

        receipt["status"] = "authoritative_catalog_control_snapshotted_not_thematic_payload"
        (out / "acquisition_receipt.json").write_text(json.dumps(receipt, indent=2), encoding="utf-8")
        print(json.dumps(receipt, indent=2))
        return 0

    except Exception as exc:
        receipt.update(
            {
                "status": "blocked_external_authoritative_catalog_api_access",
                "raw_control_response_acquired": False,
                "sha256_available": False,
                "observed_schema_available": False,
                "error_type": type(exc).__name__,
                "error": str(exc)[:1000],
                "resolution_rule": "Retry only the exact authoritative OGD control/catalog path or a resource endpoint explicitly resolved from authoritative metadata. Do not use mirrors, guessed resource IDs, scraped rankings, or name-only geography linkage.",
            }
        )
        (out / "acquisition_blocker.json").write_text(json.dumps(receipt, indent=2), encoding="utf-8")
        print(json.dumps(receipt, indent=2))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
