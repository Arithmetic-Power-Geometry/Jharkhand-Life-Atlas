#!/usr/bin/env python3
"""Fail-closed acquisition probe for the official OGD quarterly HMIS facility-extremes catalog.

This script snapshots only bytes returned by the exact authoritative OGD control URL pinned
in sources.yaml. It records SHA-256 and classifies the *observed* response rather than
assuming that an `/apis/<uuid>` URL returned machine-readable API metadata. HTML portal
shells are preserved as evidence but are explicitly non-schema-bearing and cannot satisfy
resource identity, payload acquisition, or publication gates.

No facility ranking, Jharkhand membership, geography linkage, completeness claim, missing
value interpretation, or thematic publication is inferred from catalog/control metadata.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

SOURCE_ID = "OGD_HMIS_QUARTERLY_FACILITY_EXTREMES_2026"
CATALOG_ID = "efc4b11e-30ca-4e02-a168-902d34c2e7a0"
AUTHORITY = "Ministry of Health and Family Welfare, Department of Health and Family Welfare, Government of India"
CATALOG_PAGE = "https://www.data.gov.in/catalog/all-india-level-quarterly-maximum-and-minimum-performing-public-health-facilities-selected"
CONTROL_URL = f"https://www.data.gov.in/apis/{CATALOG_ID}"
UUID_RE = re.compile(r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b", re.I)
TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.I | re.S)
RESOURCE_HREF_RE = re.compile(r"href=[\"']([^\"']*(?:/resource/|/resources/)[^\"']*)[\"']", re.I)


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


def classify_observed_response(payload: bytes, content_type: str | None) -> dict[str, Any]:
    """Classify response bytes conservatively and inventory identifiers without promotion."""
    text = payload.decode("utf-8", errors="ignore")
    lowered_type = (content_type or "").lower()

    try:
        structured = json.loads(text)
    except (ValueError, TypeError):
        structured = None

    if structured is not None:
        return {
            "observed_response_kind": "structured_json",
            "structured_json_observed": True,
            "observed_json_shape": json_shape(structured),
            "observed_schema_available": False,
            "machine_resource_identity_resolved": False,
        }

    looks_html = "text/html" in lowered_type or "<html" in text[:10000].lower() or "<!doctype html" in text[:10000].lower()
    if looks_html:
        title_match = TITLE_RE.search(text)
        title = re.sub(r"\s+", " ", title_match.group(1)).strip() if title_match else None
        uuids = list(dict.fromkeys(UUID_RE.findall(text)))[:100]
        hrefs = list(dict.fromkeys(RESOURCE_HREF_RE.findall(text)))[:100]
        explicit_resource_uuids = [u for u in uuids if u.lower() != CATALOG_ID.lower()]
        return {
            "observed_response_kind": "html_portal_shell",
            "structured_json_observed": False,
            "html_title": title,
            "observed_uuid_count": len(uuids),
            "observed_uuids": uuids,
            "observed_resource_href_count": len(hrefs),
            "observed_resource_hrefs": hrefs,
            "explicit_resource_uuid_candidates": explicit_resource_uuids,
            "observed_schema_available": False,
            "machine_resource_identity_resolved": False,
        }

    return {
        "observed_response_kind": "opaque_non_json_non_html",
        "structured_json_observed": False,
        "observed_schema_available": False,
        "machine_resource_identity_resolved": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--timeout", type=float, default=45.0)
    args = parser.parse_args()

    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    observed_at = datetime.now(timezone.utc).isoformat()

    receipt: dict[str, Any] = {
        "contract": "JLA_SOURCE_PROBE_V2",
        "source_id": SOURCE_ID,
        "authority": AUTHORITY,
        "catalog_id": CATALOG_ID,
        "catalog_page": CATALOG_PAGE,
        "control_url": CONTROL_URL,
        "observed_at_utc": observed_at,
        "publication_allowed": False,
        "curated_output_created": False,
        "raw_thematic_payload_acquired": False,
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

        inventory = classify_observed_response(payload, receipt.get("content_type"))
        receipt.update(inventory)
        (out / "observed_response_inventory.json").write_text(
            json.dumps(inventory, indent=2, sort_keys=True), encoding="utf-8"
        )
        if inventory.get("structured_json_observed"):
            (out / "observed_json_shape.json").write_text(
                json.dumps(inventory.get("observed_json_shape"), indent=2, sort_keys=True), encoding="utf-8"
            )

        if inventory["observed_response_kind"] == "html_portal_shell":
            receipt["status"] = "authoritative_control_snapshotted_html_shell_not_machine_resource_metadata"
            receipt["resolution_rule"] = (
                "Preserve this response as immutable control evidence only. Continue to an exact official resource/download "
                "endpoint explicitly exposed by authoritative metadata; never synthesize a resource UUID from the catalog UUID, title, slug, or HTML shell."
            )
        elif inventory["observed_response_kind"] == "structured_json":
            receipt["status"] = "authoritative_catalog_control_json_snapshotted_not_thematic_payload"
        else:
            receipt["status"] = "authoritative_catalog_control_opaque_snapshot_not_thematic_payload"

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
                "machine_resource_identity_resolved": False,
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
