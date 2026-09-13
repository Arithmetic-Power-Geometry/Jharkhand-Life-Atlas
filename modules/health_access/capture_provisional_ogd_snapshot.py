"""Capture an explicit authoritative OGD payload as a non-canonical evidence snapshot.

This step preserves exact bytes only inside the ephemeral CI workspace and records a
cryptographic/schema receipt. It MUST NOT resolve source-identity ambiguity, publish
raw source bytes, or enable publication. The receipt includes a header-only privacy
risk audit so person/contact-bearing sources remain fail-closed before curation.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

import requests

CONTRACT = "JLA_PROVISIONAL_OGD_SNAPSHOT_V2"
MAX_BYTES = 100 * 1024 * 1024
USER_AGENT = "Jharkhand-Life-Atlas governed-source-acquisition/1.0"


def _official(url: str) -> bool:
    host = urlparse(url).netloc.casefold().split(":", 1)[0]
    return url.startswith("https://") and (host in {"data.gov.in", "www.data.gov.in"} or host.endswith(".data.gov.in"))


def _looks_like_html(raw_path: Path) -> bool:
    with raw_path.open("rb") as f:
        prefix = f.read(4096).lstrip().lower()
    return prefix.startswith(b"<!doctype html") or prefix.startswith(b"<html") or b"<html" in prefix[:1024]


def _normalized_header(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.casefold()).strip()


def _privacy_risk_columns(header: list[str]) -> list[dict[str, str]]:
    """Classify header names only; never inspect/store row values for this audit."""
    rules = (
        ("email", ("email", "e mail")),
        ("telephone", ("telephone", "phone")),
        ("mobile", ("mobile",)),
        ("named_person", ("nodal person", "contact person", "contact name", "person name")),
    )
    findings: list[dict[str, str]] = []
    for column in header:
        normalized = _normalized_header(column)
        for category, needles in rules:
            if any(needle in normalized for needle in needles):
                findings.append({"column": column, "category": category})
                break
    return findings


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
    if _looks_like_html(raw_path):
        raise RuntimeError("authoritative endpoint returned HTML rather than a CSV payload")

    # Candidate-level schema observation only. No derived/public dataset is produced.
    # Decode strictly: malformed bytes must not be silently replaced and then treated as
    # an observed schema. Row values are never copied into the receipt or logs.
    try:
        with raw_path.open("r", encoding="utf-8-sig", errors="strict", newline="") as f:
            reader = csv.reader(f)
            header = next(reader, [])
            if not header or not any(cell.strip() for cell in header):
                raise RuntimeError("CSV payload has no non-empty header")
            row_count = 0
            width_mismatch_count = 0
            for row in reader:
                row_count += 1
                if len(row) != len(header):
                    width_mismatch_count += 1
    except UnicodeDecodeError as exc:
        raise RuntimeError("CSV payload is not valid UTF-8/UTF-8-SIG") from exc

    privacy_columns = _privacy_risk_columns(header)
    return {
        "contract": CONTRACT,
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "requested_url": url,
        "final_url": final_url,
        "content_type": content_type,
        "byte_count": n,
        "sha256": h.hexdigest(),
        "raw_snapshot_persisted": True,
        "raw_snapshot_scope": "ephemeral_ci_workspace_only_not_artifact_export",
        "raw_snapshot_filename": raw_path.name,
        "payload_format_guarded": True,
        "schema_inspected": True,
        "observed_columns": header,
        "observed_column_count": len(header),
        "observed_data_row_count": row_count,
        "observed_row_width_mismatch_count": width_mismatch_count,
        "row_values_recorded_in_receipt": False,
        "privacy_header_audit_performed": True,
        "privacy_risk_columns": privacy_columns,
        "privacy_risk_column_count": len(privacy_columns),
        "privacy_review_required": bool(privacy_columns),
        "canonical_source_identity_resolved": False,
        "publication_allowed": False,
        "curated_dataset_emitted": False,
        "rules": [
            "snapshot_is_candidate_level_evidence_not_canonical_source_selection",
            "exact_bytes_and_sha256_must_travel_together_inside_governed_processing",
            "raw_candidate_bytes_must_not_be_exported_as_ci_artifacts",
            "receipt_must_not_contain_source_row_values",
            "privacy_risk_columns_require_exclusion_or_explicit_rights_and_safety_review_before_any_public_projection",
            "html_or_malformed_text_must_never_be_treated_as_csv_evidence",
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
