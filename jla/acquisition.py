from pathlib import Path

import polars as pl
import yaml

ROOT = Path(__file__).resolve().parents[1]
QUEUE_PATH = ROOT / "config" / "acquisition_queue.yaml"


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
