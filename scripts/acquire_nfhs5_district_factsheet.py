#!/usr/bin/env python3
"""Acquire the authoritative NFHS-5 district factsheet workbook fail-closed.

This helper never marks a source publishable. It only accepts an explicit HTTPS
`data.gov.in` URL, writes bytes atomically, computes SHA-256, records retrieval
metadata, and emits a manifest suitable for subsequent schema/provenance review.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_URL = (
    "https://data.gov.in/files/ogdpv2dms/s3fs-public/datafile/"
    "NFHS_5_India_Districts_Factsheet_Data.xls"
)


def validate_authoritative_url(url: str) -> None:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in {"data.gov.in", "www.data.gov.in"}:
        raise ValueError("refusing non-authoritative or non-HTTPS payload URL")
    if not parsed.path.lower().endswith((".xls", ".xlsx")):
        raise ValueError("NFHS-5 district factsheet payload must be an Excel workbook")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def acquire(url: str, output: Path, timeout: int = 90) -> dict:
    validate_authoritative_url(url)
    output.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "Jharkhand-Life-Atlas/1.0 (+https://github.com/Arithmetic-Power-Geometry/Jharkhand-Life-Atlas)"},
    )
    retrieved_at = datetime.now(timezone.utc).isoformat()
    fd, temporary_name = tempfile.mkstemp(prefix=output.name + ".", dir=output.parent)
    os.close(fd)
    temporary = Path(temporary_name)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response, temporary.open("wb") as sink:
            content_type = response.headers.get("Content-Type")
            final_url = response.geturl()
            validate_authoritative_url(final_url)
            total = 0
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                sink.write(chunk)
                total += len(chunk)
        if total == 0:
            raise RuntimeError("authoritative endpoint returned an empty payload")
        temporary.replace(output)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise

    return {
        "source_id": "OGD_NFHS5_DISTRICT_FACTSHEETS_2019_2021",
        "retrieved_at_utc": retrieved_at,
        "requested_url": url,
        "final_url": final_url,
        "bytes": output.stat().st_size,
        "sha256": sha256_file(output),
        "content_type": content_type,
        "raw_path": str(output),
        "schema_inspected": False,
        "publication_allowed": False,
        "missing_value_policy": "preserve_as_null_never_coerce_to_zero",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument("--output", type=Path, default=Path("data/raw/health_access/NFHS_5_India_Districts_Factsheet_Data.xls"))
    parser.add_argument("--manifest", type=Path, default=Path("artifacts/health_access/nfhs5_district_acquisition_manifest.json"))
    args = parser.parse_args()

    manifest = acquire(args.url, args.output)
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
