"""Acquire authoritative SBM-G sanitation state-level context from OGD.

Fail-closed by design: links are resolved only from the registered official
OGD resource page, accepted payloads must remain on a *.data.gov.in host,
bytes are hashed before inspection, blanks remain null, and only an explicitly
labelled Jharkhand row is extracted. State-level counts are never disaggregated.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse

import requests

SOURCE_ID = "OGD_SBMG_IHHL_CSC_2024_25"
RESOURCE_PAGE = "https://ap.data.gov.in/resource/stateut-wise-number-households-individual-household-latrines-ihhls-and-community-sanitary"
AUTHORITY = "Government of India Open Government Data Platform / Rajya Sabha"
REPORTING_PERIOD = "2024-25"
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0 Safari/537.36"


def _norm(value: object) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(value or "").strip().casefold()).strip("_")


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _ogd_host(url: str) -> bool:
    parsed = urlparse(url)
    host = (parsed.hostname or "").casefold()
    return parsed.scheme == "https" and (host == "data.gov.in" or host.endswith(".data.gov.in"))


def _looks_html(data: bytes, content_type: str = "") -> bool:
    prefix = data[:512].lstrip().lower()
    return "text/html" in content_type.casefold() or prefix.startswith(b"<!doctype html") or prefix.startswith(b"<html")


class _Links(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.hrefs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.casefold() != "a":
            return
        for key, value in attrs:
            if key.casefold() == "href" and value:
                self.hrefs.append(value)


def _candidate_links(base_url: str, html: str) -> list[str]:
    parser = _Links()
    parser.feed(html)
    out: list[str] = []
    for href in parser.hrefs:
        absolute = urljoin(base_url, href)
        low = absolute.casefold()
        if not _ogd_host(absolute):
            continue
        if any(token in low for token in (".csv", "download", "datafile", "export")) and absolute not in out:
            out.append(absolute)
    return out


def _parse_csv(data: bytes) -> tuple[list[str], list[dict[str, str | None]]]:
    text = data.decode("utf-8-sig", errors="strict")
    sample = text[:8192]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
    except csv.Error:
        dialect = csv.excel
    reader = csv.DictReader(io.StringIO(text), dialect=dialect)
    fields = [str(x).strip() for x in (reader.fieldnames or [])]
    rows = [{str(k).strip(): (v if v not in (None, "") else None) for k, v in row.items()} for row in reader]
    if len(fields) < 3 or not rows:
        raise RuntimeError("Official SBM-G CSV has an implausible observed schema or no rows")
    return fields, rows


def _state_column(fields: list[str]) -> str:
    exact = {_norm(f): f for f in fields}
    for key in ("state_ut", "state", "state_ut_name", "state_name", "states_uts"):
        if key in exact:
            return exact[key]
    candidates = [f for f in fields if "state" in _norm(f) and "code" not in _norm(f)]
    if len(candidates) == 1:
        return candidates[0]
    raise RuntimeError(f"Could not uniquely identify State/UT column from observed fields: {fields}")


def acquire(output_dir: Path) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT, "Accept-Language": "en-US,en;q=0.9", "Cache-Control": "no-cache"})
    attempts: list[dict[str, Any]] = []

    landing = session.get(RESOURCE_PAGE, timeout=90, allow_redirects=True)
    attempts.append({"stage": "resource_page", "status_code": landing.status_code, "final_url": landing.url, "bytes_received": len(landing.content)})
    landing.raise_for_status()
    if not _ogd_host(landing.url):
        raise RuntimeError(f"Registered OGD resource redirected outside *.data.gov.in: {landing.url}")

    candidates = _candidate_links(landing.url, landing.text)
    if not candidates:
        raise RuntimeError("No authoritative CSV/download candidate exposed by the official OGD resource page; refusing to infer a payload URL")

    payload: bytes | None = None
    final_url: str | None = None
    for candidate in candidates:
        try:
            response = session.get(candidate, headers={"Referer": landing.url, "Accept": "text/csv,application/csv,application/octet-stream,*/*;q=0.5"}, timeout=120, allow_redirects=True)
            attempts.append({"stage": "official_asset", "requested_url": candidate, "status_code": response.status_code, "final_url": response.url, "bytes_received": len(response.content), "content_type": response.headers.get("Content-Type", "")})
            if response.status_code != 200 or not response.content or _looks_html(response.content, response.headers.get("Content-Type", "")):
                continue
            if not _ogd_host(response.url):
                continue
            payload, final_url = response.content, response.url
            break
        except requests.RequestException as exc:
            attempts.append({"stage": "official_asset", "requested_url": candidate, "error": f"{type(exc).__name__}: {exc}"})

    if payload is None or final_url is None:
        raise RuntimeError("Authoritative SBM-G payload acquisition failed; no mirror or inferred payload accepted. attempts=" + json.dumps(attempts, ensure_ascii=False))
    if len(payload) < 500:
        raise RuntimeError(f"Official SBM-G payload is implausibly small: {len(payload)} bytes")

    fields, rows = _parse_csv(payload)
    state_col = _state_column(fields)
    jh = [row for row in rows if _norm(row.get(state_col)) == "jharkhand"]
    if len(jh) != 1:
        raise RuntimeError(f"Expected exactly one explicit Jharkhand row; observed {len(jh)}")

    raw_path = output_dir / "sbmg_ihhl_csc_2024_25.csv"
    raw_path.write_bytes(payload)
    schema = {
        "contract": "JLA_OBSERVED_SCHEMA_V1",
        "source_id": SOURCE_ID,
        "observed_fields": fields,
        "row_count": len(rows),
        "state_column": state_col,
        "jharkhand_rows": 1,
        "missing_cells": sum(1 for row in rows for value in row.values() if value is None),
    }
    (output_dir / "sbmg_observed_schema.json").write_text(json.dumps(schema, indent=2, ensure_ascii=False), encoding="utf-8")
    (output_dir / "sbmg_jharkhand_state_context.json").write_text(json.dumps(jh[0], indent=2, ensure_ascii=False), encoding="utf-8")

    receipt = {
        "contract": "JLA_SOURCE_SNAPSHOT_V1",
        "source_id": SOURCE_ID,
        "authority": AUTHORITY,
        "resource_page": RESOURCE_PAGE,
        "final_official_payload_url": final_url,
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "reporting_period": REPORTING_PERIOD,
        "byte_count": len(payload),
        "sha256": _sha256(payload),
        "raw_filename": raw_path.name,
        "acquisition_attempts": attempts,
        "rights": {"status": "pending_exact_resource_GODL_attribution_review", "publication_allowed": False},
        "geography": {"source_granularity": "state_ut", "lower_geography_disaggregation_allowed": False, "direct_name_equivalence_to_other_vintages_allowed": False},
        "semantics": "IHHL/CSC construction counts are not evidence of functionality, usage, sanitation quality, or ODF sustainability",
        "null_semantics": "source blanks retained as null; no missing-to-zero conversion",
        "publication_allowed": False,
        "publication_blocker": "requires resource-level rights/attribution review, unit/period validation and cannot support lower-geography sanitation outputs",
    }
    (output_dir / "sbmg_acquisition_receipt.json").write_text(json.dumps(receipt, indent=2, ensure_ascii=False), encoding="utf-8")
    return receipt


def main() -> None:
    parser = argparse.ArgumentParser(description="Acquire authoritative OGD SBM-G state sanitation context")
    parser.add_argument("--output-dir", type=Path, default=Path("build/sanitation_sbmg"))
    args = parser.parse_args()
    print(json.dumps(acquire(args.output_dir), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
