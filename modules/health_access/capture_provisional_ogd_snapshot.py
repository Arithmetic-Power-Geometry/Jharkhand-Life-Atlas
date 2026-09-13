"""Capture an explicit authoritative OGD payload as a non-canonical evidence snapshot.

This step preserves exact bytes and records a cryptographic receipt, but it MUST NOT
resolve source-identity ambiguity or enable publication. It is intended to advance
schema inspection and reproducibility while multiple explicit official aliases remain
unresolved.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import requests

CONTRACT = "JLA_PROVISIONAL_OGD_SNAPSHOT_V1"
MAX_BYTES = 100 * 1024 * 1024
USER_AGENT = "Jharkhand-Life-Atlas governed-source-acquisition/1.0"


def _official(url: str) -> bool:
    host = urlparse(url).netloc.casefold().split(":", 1)[0]
    return url.startswith("https://") and (host in {"data.gov.in", "www.data.gov.in"} or host.endswith(".data.gov.in"))


def capture(url: str, raw_path: Path) -> dict:
    if not _official(url):
        raise ValueError("source must be an explicit HTTPS data.gov.in URL")
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    h = hashlib.sha256()
    n = 0
    with requests.get(url, timeout=120, allow_redirects=True, stream=True,
                      headers={"User-Agent": USER_AGENT, "Accept": "text/csv,text/plain,*/*;q=0.5"}) as r:
        r.raise_for_status()
        if not _official(r.url):
            raise RuntimeError("redirect left authoritative data.gov.in host")
        with raw_path.open("wb") as f:
            for chunk in r.iter_content(1024 * 1024):
                if not chunk:
                    continue
                n += len(chunk)
                if n > MAX_BYTES:
                    raise RuntimeError("payload exceeds 100 MiB safety limit")
                h.update(chunk)
                f.write(chunk)
        content_type = r.headers.get("Content-Type", "")
        final_url = r.url
    if n == 0:
        raise RuntimeError("empty payload")

    # Candidate-level schema observation only. No derived/public dataset is produced.
    with raw_path.open("r", encoding="utf-8-sig", errors="replace", newline="") as f:
        reader = csv.reader(f)
        header = next(reader, [])
        sample_rows = []
        row_count = 0
        for row in reader:
            row_count += 1
            if len(sample_rows) < 5:
                sample_rows.append(row)

    return {
        "contract": CONTRACT,
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "requested_url": url,
        "final_url": final_url,
        "content_type": content_type,
        "byte_count": n,
        "sha256": h.hexdigest(),
        "raw_snapshot_persisted": True,
        "raw_snapshot_filename": raw_path.name,
        "schema_inspected": True,
        "observed_columns": header,
        "observed_column_count": len(header),
        "observed_data_row_count": row_count,
        "sample_row_count": len(sample_rows),
        "canonical_source_identity_resolved": False,
        "publication_allowed": False,
        "curated_dataset_emitted": False,
        "rules": [
            "snapshot_is_candidate_level_evidence_not_canonical_source_selection",
            "exact_bytes_and_sha256_must_travel_together",
            "schema_observation_does_not_authorize_publication",
            "no_geographic_equivalence_may_be_inferred_from_names_alone",
            "missing_values_must_remain_missing_and_must_never_be_silently_zero_filled",
            "no_person_level_sensitive_data_may_be_published",
        ],
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--url", required=True)
    p.add_argument("--raw", type=Path, required=True)
    p.add_argument("--receipt", type=Path, required=True)
    a = p.parse_args()
    receipt = capture(a.url, a.raw)
    a.receipt.parent.mkdir(parents=True, exist_ok=True)
    a.receipt.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
