"""Audit byte equivalence of explicit authoritative OGD payload candidates.

This audit is deliberately narrower than payload acquisition. It streams each already-
observed official candidate, records retrieval metadata and SHA-256, and decides whether
multiple explicit candidates are byte-identical. When a governed payload binding is
provided, URL selection is permitted only if every candidate is byte-identical *and*
that shared payload matches the governed SHA-256/byte count. This prevents two official
aliases drifting together to new bytes from being mistaken for evidence about the
already-governed candidate. It never persists raw bytes, never inspects schema, and
never enables publication.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import requests

CONTRACT = "JLA_OGD_PAYLOAD_CANDIDATE_EQUIVALENCE_V1"
MAX_BYTES = 100 * 1024 * 1024
USER_AGENT = "Jharkhand-Life-Atlas governed-source-audit/1.0"


def _official_host(url: str) -> bool:
    host = urlparse(url).netloc.casefold().split(":", 1)[0]
    return host in {"data.gov.in", "www.data.gov.in"} or host.endswith(".data.gov.in")


def _fetch_candidate(session: requests.Session, url: str) -> dict[str, Any]:
    record: dict[str, Any] = {
        "requested_url": url,
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "eligible_for_equivalence": False,
        "sha256": None,
        "byte_count": None,
    }
    if not url.startswith("https://") or not _official_host(url):
        record["error"] = "candidate_not_on_authoritative_data_gov_in_https_host"
        return record

    try:
        with session.get(url, timeout=120, allow_redirects=True, stream=True) as response:
            record.update(
                {
                    "status_code": response.status_code,
                    "final_url": response.url,
                    "content_type": response.headers.get("Content-Type", ""),
                }
            )
            if response.status_code != 200:
                record["error"] = f"http_status_{response.status_code}"
                return record
            if not response.url.startswith("https://") or not _official_host(response.url):
                record["error"] = "final_url_left_authoritative_data_gov_in_host"
                return record

            digest = hashlib.sha256()
            size = 0
            for chunk in response.iter_content(chunk_size=1024 * 1024):
                if not chunk:
                    continue
                size += len(chunk)
                if size > MAX_BYTES:
                    record["error"] = "payload_exceeded_100_mib_audit_limit"
                    return record
                digest.update(chunk)

            if size <= 0:
                record["error"] = "empty_payload"
                return record
            record["byte_count"] = size
            record["sha256"] = digest.hexdigest()
            record["eligible_for_equivalence"] = True
            return record
    except requests.RequestException as exc:
        record["error"] = f"{type(exc).__name__}: {exc}"
        return record


def _validate_expected_binding(expected_sha256: str | None, expected_byte_count: int | None) -> None:
    if (expected_sha256 is None) != (expected_byte_count is None):
        raise ValueError("expected_sha256 and expected_byte_count must be supplied together")
    if expected_sha256 is None:
        return
    digest = expected_sha256.strip().casefold()
    if len(digest) != 64 or any(ch not in "0123456789abcdef" for ch in digest):
        raise ValueError("expected_sha256 must be a 64-character hexadecimal SHA-256 digest")
    if expected_byte_count is None or expected_byte_count <= 0:
        raise ValueError("expected_byte_count must be positive")


def evaluate_candidate_records(
    records: list[dict[str, Any]],
    expected_sha256: str | None = None,
    expected_byte_count: int | None = None,
) -> dict[str, Any]:
    """Evaluate candidates without inventing equivalence from partial or drifted evidence."""
    _validate_expected_binding(expected_sha256, expected_byte_count)
    governed_binding_required = expected_sha256 is not None
    expected_sha256_normalized = expected_sha256.strip().casefold() if expected_sha256 else None

    base = {
        "governed_binding_required": governed_binding_required,
        "expected_sha256": expected_sha256_normalized,
        "expected_byte_count": expected_byte_count,
        "governed_binding_verified": None,
    }

    all_verified = len(records) >= 2 and all(r.get("eligible_for_equivalence") is True for r in records)
    if not all_verified:
        return {
            **base,
            "all_candidates_verified": False,
            "byte_identical": None,
            "canonical_selection_permitted": False,
            "deterministic_preferred_candidate_url": None,
            "shared_sha256": None,
            "shared_byte_count": None,
        }

    hashes = {str(r.get("sha256")).casefold() for r in records}
    sizes = {int(r.get("byte_count")) for r in records}
    identical = len(hashes) == 1 and len(sizes) == 1
    if not identical:
        return {
            **base,
            "all_candidates_verified": True,
            "byte_identical": False,
            "governed_binding_verified": False if governed_binding_required else None,
            "canonical_selection_permitted": False,
            "deterministic_preferred_candidate_url": None,
            "shared_sha256": None,
            "shared_byte_count": None,
        }

    shared_sha256 = next(iter(hashes))
    shared_byte_count = next(iter(sizes))
    governed_binding_verified = (
        shared_sha256 == expected_sha256_normalized and shared_byte_count == expected_byte_count
        if governed_binding_required
        else None
    )
    selection_permitted = identical and (governed_binding_verified is not False)

    return {
        **base,
        "all_candidates_verified": True,
        "byte_identical": True,
        "governed_binding_verified": governed_binding_verified,
        "canonical_selection_permitted": selection_permitted,
        "deterministic_preferred_candidate_url": (
            sorted(str(r["requested_url"]) for r in records)[0] if selection_permitted else None
        ),
        "shared_sha256": shared_sha256,
        "shared_byte_count": shared_byte_count,
    }


def audit(
    source_id: str,
    candidates: list[str],
    expected_sha256: str | None = None,
    expected_byte_count: int | None = None,
) -> dict[str, Any]:
    if len(set(candidates)) < 2:
        raise ValueError("at least two distinct explicit candidates are required")
    _validate_expected_binding(expected_sha256, expected_byte_count)
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT, "Accept": "text/csv,text/plain,*/*;q=0.5"})
    records = [_fetch_candidate(session, url) for url in candidates]
    decision = evaluate_candidate_records(records, expected_sha256, expected_byte_count)
    return {
        "contract": CONTRACT,
        "source_id": source_id,
        "checked_at_utc": datetime.now(timezone.utc).isoformat(),
        "candidates": records,
        **decision,
        "raw_snapshot_persisted": False,
        "raw_payload_acquired": False,
        "schema_inspected": False,
        "publication_allowed": False,
        "rules": [
            "only_explicit_authoritative_candidates_may_be_audited",
            "multiple_candidates_require_all_successful_hashes_before_equivalence",
            "hash_mismatch_keeps_identity_ambiguous",
            "partial_or_failed_retrieval_keeps_identity_ambiguous",
            "when_governed_binding_is_supplied_shared_bytes_must_match_expected_sha256_and_byte_count",
            "two_official_aliases_drifting_together_do_not_validate_the_governed_candidate",
            "byte_equivalence_verification_is_not_raw_snapshot_acquisition",
            "byte_equivalence_verification_is_not_schema_validation",
            "byte_equivalence_verification_does_not_enable_publication",
            "missing_values_are_never_converted_to_zero",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-id", required=True)
    parser.add_argument("--candidate", action="append", required=True)
    parser.add_argument("--expected-sha256")
    parser.add_argument("--expected-byte-count", type=int)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = audit(
        args.source_id,
        args.candidate,
        expected_sha256=args.expected_sha256,
        expected_byte_count=args.expected_byte_count,
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
