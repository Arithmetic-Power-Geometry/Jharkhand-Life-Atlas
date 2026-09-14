import json
from pathlib import Path

import polars as pl
import yaml

ROOT = Path(__file__).resolve().parents[1]
QUEUE_PATH = ROOT / "config" / "acquisition_queue.yaml"
HEALTH_IDENTITY_PATH = ROOT / "modules" / "health_access" / "resource_identity_registry.yaml"
HEALTH_PRIMARY_BINDING_PATH = (
    ROOT / "modules" / "health_access" / "evidence" / "nhd_primary_payload_binding_2026-09-14.json"
)


def acquisition_queue() -> pl.DataFrame:
    """Return the controlled evidence-acquisition queue for public status display.

    This function exposes repository truth only. It does not infer acquisition or
    publication readiness from source discovery.
    """
    payload = yaml.safe_load(QUEUE_PATH.read_text(encoding="utf-8")) or {}
    rows = []
    for item in payload.get("workstreams", []):
        rows.append(
            {
                "priority": item.get("rank"),
                "module": item.get("module_id"),
                "source": item.get("source_id"),
                "objective": str(item.get("objective", "")).replace("_", " "),
                "state": str(item.get("current_state", "")).replace("_", " "),
                "publication_allowed": bool(item.get("publication_allowed", False)),
                "evidence_remaining": ", ".join(
                    str(value).replace("_", " ") for value in item.get("next_evidence", [])
                ),
            }
        )
    if not rows:
        return pl.DataFrame(
            schema={
                "priority": pl.Int64,
                "module": pl.String,
                "source": pl.String,
                "objective": pl.String,
                "state": pl.String,
                "publication_allowed": pl.Boolean,
                "evidence_remaining": pl.String,
            }
        )
    return pl.DataFrame(rows).sort("priority")


def acquisition_queue_status() -> dict:
    payload = yaml.safe_load(QUEUE_PATH.read_text(encoding="utf-8")) or {}
    return {
        "queue_id": payload.get("queue_id"),
        "status": payload.get("status"),
        "workstream_count": len(payload.get("workstreams", [])),
        "execution_rules": payload.get("execution_rules", []),
    }


def _verified_primary_health_binding() -> dict:
    """Return durable aggregate-only evidence for the verified primary NHD payload.

    The receipt is intentionally separate from the older resource-identity registry:
    exact authoritative bytes were verified later, while canonical alias/machine-ID
    resolution remains open. This function never promotes that byte binding to
    publication readiness, temporal validity, semantic validity, or geography linkage.
    """
    if not HEALTH_PRIMARY_BINDING_PATH.exists():
        return {}
    try:
        receipt = json.loads(HEALTH_PRIMARY_BINDING_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}

    primary = receipt.get("primary_authoritative_candidate", {}) or {}
    decision = receipt.get("decision", {}) or {}
    boundary = receipt.get("scientific_boundary", {}) or {}
    verified = bool(
        primary.get("exact_governed_payload_binding_verified")
        and primary.get("matches_governed_candidate_sha256")
        and primary.get("matches_governed_candidate_byte_count")
        and decision.get("primary_official_payload_binding_can_be_treated_as_verified")
    )
    return {
        "source_id": receipt.get("source_id"),
        "verified": verified,
        "sha256": primary.get("sha256") if verified else None,
        "byte_count": primary.get("byte_count") if verified else None,
        "requested_url": primary.get("requested_url") if verified else None,
        "canonical_alias_selection_permitted": bool(
            boundary.get("canonical_alias_selection_permitted", False)
        ),
        "publication_allowed": bool(receipt.get("publication_allowed", False)),
    }


def health_resource_identities() -> pl.DataFrame:
    """Expose Health resource-identity state directly from governed repository evidence.

    Resource-page discovery is intentionally distinct from machine payload identity,
    byte acquisition and publication eligibility. A later exact byte-level binding may
    establish that one explicit official payload was acquired even while the canonical
    machine identity/alias remains unresolved. Null identifiers stay null; no identity
    is inferred from names or URLs.
    """
    payload = yaml.safe_load(HEALTH_IDENTITY_PATH.read_text(encoding="utf-8")) or {}
    binding = _verified_primary_health_binding()
    rows = []
    for item in payload.get("resources", []):
        binding_applies = bool(
            binding.get("verified") and binding.get("source_id") == item.get("source_id")
        )
        rows.append(
            {
                "source": item.get("source_id"),
                "resource_page_state": str(item.get("resource_page_identity_state", "")).replace("_", " "),
                "machine_payload_state": str(item.get("machine_payload_identity_state", "")).replace("_", " "),
                "machine_resource_id": item.get("machine_resource_id"),
                "raw_payload_acquired": bool(item.get("raw_payload_acquired", False) or binding_applies),
                "official_payload_binding_verified": binding_applies,
                "raw_sha256": binding.get("sha256") if binding_applies else item.get("raw_sha256"),
                "raw_bytes": binding.get("byte_count") if binding_applies else item.get("raw_bytes"),
                "schema_inspected": bool(item.get("schema_inspected", False)),
                "publication_allowed": bool(item.get("publication_allowed", False)) and not binding_applies,
                "official_updated_on": item.get("live_catalog_updated_on"),
                "resource_url": item.get("canonical_resource_url"),
            }
        )
    if not rows:
        return pl.DataFrame(
            schema={
                "source": pl.String,
                "resource_page_state": pl.String,
                "machine_payload_state": pl.String,
                "machine_resource_id": pl.String,
                "raw_payload_acquired": pl.Boolean,
                "official_payload_binding_verified": pl.Boolean,
                "raw_sha256": pl.String,
                "raw_bytes": pl.Int64,
                "schema_inspected": pl.Boolean,
                "publication_allowed": pl.Boolean,
                "official_updated_on": pl.String,
                "resource_url": pl.String,
            }
        )
    return pl.DataFrame(rows)


def health_resource_identity_status() -> dict:
    payload = yaml.safe_load(HEALTH_IDENTITY_PATH.read_text(encoding="utf-8")) or {}
    resources = payload.get("resources", [])
    frame = health_resource_identities()
    acquired = int(frame["raw_payload_acquired"].sum()) if frame.height else 0
    bindings = int(frame["official_payload_binding_verified"].sum()) if frame.height else 0
    resolved = sum(
        item.get("machine_payload_identity_state") in {"resolved_unretrieved", "acquired_verified"}
        for item in resources
    )
    publishable = int(frame["publication_allowed"].sum()) if frame.height else 0
    return {
        "registry_id": payload.get("registry_id"),
        "resource_count": len(resources),
        "machine_identities_resolved": resolved,
        "raw_payloads_acquired": acquired,
        "official_payload_bindings_verified": bindings,
        "publishable_resources": publishable,
    }
