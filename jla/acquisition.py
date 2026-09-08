from pathlib import Path

import polars as pl
import yaml

ROOT = Path(__file__).resolve().parents[1]
QUEUE_PATH = ROOT / "config" / "acquisition_queue.yaml"
HEALTH_IDENTITY_PATH = ROOT / "modules" / "health_access" / "resource_identity_registry.yaml"


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


def health_resource_identities() -> pl.DataFrame:
    """Expose Health resource-identity state directly from the governed registry.

    Resource-page discovery is intentionally distinct from machine payload identity,
    byte acquisition and publication eligibility. Null machine identifiers are kept
    as null rather than replaced with guessed values.
    """
    payload = yaml.safe_load(HEALTH_IDENTITY_PATH.read_text(encoding="utf-8")) or {}
    rows = []
    for item in payload.get("resources", []):
        rows.append(
            {
                "source": item.get("source_id"),
                "resource_page_state": str(item.get("resource_page_identity_state", "")).replace("_", " "),
                "machine_payload_state": str(item.get("machine_payload_identity_state", "")).replace("_", " "),
                "machine_resource_id": item.get("machine_resource_id"),
                "raw_payload_acquired": bool(item.get("raw_payload_acquired", False)),
                "schema_inspected": bool(item.get("schema_inspected", False)),
                "publication_allowed": bool(item.get("publication_allowed", False)),
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
    acquired = sum(bool(item.get("raw_payload_acquired", False)) for item in resources)
    resolved = sum(
        item.get("machine_payload_identity_state") in {"resolved_unretrieved", "acquired_verified"}
        for item in resources
    )
    publishable = sum(bool(item.get("publication_allowed", False)) for item in resources)
    return {
        "registry_id": payload.get("registry_id"),
        "resource_count": len(resources),
        "machine_identities_resolved": resolved,
        "raw_payloads_acquired": acquired,
        "publishable_resources": publishable,
    }
