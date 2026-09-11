"""Acquire the exact official Jharkhand HMIS 2014-15 district resource fail-closed.

Starts only from the verified authoritative data.gov.in resource page. It follows
only explicit OGD machine/download links, never guesses identifiers, rejects HTML
as data, hashes any admitted payload, and records the observed CSV schema. District
aggregates remain district-level and publication stays closed pending downstream
period/geography/indicator validation.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
from datetime import datetime, timezone
from html import unescape
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests

RESOURCE_PAGE = "https://www.data.gov.in/resource/item-wise-hmis-report-district-level-jharkhand-upto-december-2014-15"
SOURCE_ID = "OGD_HMIS_JH_DISTRICT_2014_15_DECEMBER"
ALLOWED_HOSTS = {"data.gov.in", "www.data.gov.in", "api.data.gov.in"}
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/140 Safari/537.36"
HREF_RE = re.compile(r"(?:href|src)\s*=\s*[\"']([^\"']+)[\"']", re.I)
URL_RE = re.compile(r"https?://[^\s\"'<>]+", re.I)
EXPECTED_COLUMNS = ["Indicator", "S.No.", "Parameters", "Type", "District - _Jharkhand"]


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def approved(url: str) -> bool:
    try:
        return urlparse(url).hostname in ALLOWED_HOSTS
    except ValueError:
        return False


def candidate_links(html: str) -> list[str]:
    raw = [unescape(x) for x in HREF_RE.findall(html)] + [unescape(x) for x in URL_RE.findall(html)]
    out: set[str] = set()
    for link in raw:
        url = urljoin(RESOURCE_PAGE, link).replace("&amp;", "&")
        if not approved(url) or url.rstrip("/") == RESOURCE_PAGE.rstrip("/"):
            continue
        low = url.casefold()
        if any(token in low for token in (".csv", "/files/", "download", "format=csv", "api.data.gov.in/resource/")):
            out.add(url)
    return sorted(out)


def normalized_column(value: str) -> str:
    return re.sub(r"\s+", " ", value.strip()).casefold()


def inspect_csv(data: bytes, content_type: str, url: str) -> dict:
    result = {"url": url, "byte_count": len(data), "sha256": digest(data), "content_type": content_type}
    prefix = data[:512].lstrip().lower()
    if prefix.startswith(b"<!doctype html") or prefix.startswith(b"<html") or "text/html" in content_type.casefold():
        result.update({"accepted": False, "reason": "html_not_data"})
        return result
    try:
        text = data.decode("utf-8-sig")
        reader = csv.reader(io.StringIO(text))
        header = next(reader)
        if not header or len(header) < 2:
            raise ValueError("CSV header is empty or implausibly narrow")
        normalized = {normalized_column(x) for x in header}
        missing_expected = [x for x in EXPECTED_COLUMNS if normalized_column(x) not in normalized]
        sample_count = sum(1 for _, _row in zip(range(50), reader))
        if missing_expected:
            result.update({
                "accepted": False,
                "reason": "schema_does_not_match_authoritative_resource_metadata",
                "observed_columns": header,
                "missing_expected_columns": missing_expected,
                "sample_rows_read": sample_count,
            })
            return result
        result.update({
            "accepted": True,
            "format": "csv",
            "observed_columns": header,
            "authoritative_schema_fields_verified": EXPECTED_COLUMNS,
            "sample_rows_read": sample_count,
        })
        return result
    except Exception as exc:
        result.update({"accepted": False, "reason": "not_parseable_csv", "parse_error": f"{type(exc).__name__}: {exc}"})
        return result


def run(output_dir: Path) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT, "Accept-Language": "en-US,en;q=0.9"})
    report = {
        "contract": "JLA_HEALTH_HMIS_OFFICIAL_PAYLOAD_ACQUISITION_V2",
        "source_id": SOURCE_ID,
        "resource_page": RESOURCE_PAGE,
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "authoritative_resource_metadata": {
            "published_on": "2021-01-08",
            "updated_on": "2021-01-08",
            "reference_period": "2014-15_upto_december",
            "status_as_on": "2016-01-29T14:00:00+05:30",
            "granularity": "Monthly",
            "advertised_format": "csv",
            "advertised_file_size": "102 KB",
            "resource_api_state": "does_not_exist",
            "expected_columns": EXPECTED_COLUMNS,
            "provisional_figures": True,
        },
        "raw_payload_acquired": False,
        "raw_sha256": None,
        "raw_byte_count": None,
        "observed_schema": None,
        "publication_allowed": False,
        "rules": [
            "official_ogd_hosts_only",
            "never_guess_download_url_or_resource_id",
            "do_not_chase_resource_api_when_official_page_states_api_does_not_exist",
            "explicit_official_csv_link_required",
            "html_is_not_data",
            "hash_before_curation",
            "observed_schema_must_match_authoritative_resource_metadata",
            "preserve_missing_as_null",
            "district_aggregates_never_allocated_to_villages_or_facilities",
            "provisional_source_status_must_be_preserved",
            "publication_requires_period_indicator_geography_and_validation_gates",
        ],
        "attempts": [],
    }
    try:
        page = session.get(RESOURCE_PAGE, timeout=90, allow_redirects=True)
    except requests.RequestException as exc:
        report["blocker"] = f"authoritative_resource_page_request_failed:{type(exc).__name__}"
        (output_dir / "hmis_jharkhand_2014_15_acquisition.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        return report

    report.update({
        "resource_page_status": page.status_code,
        "resource_page_final_url": page.url,
        "resource_page_sha256": digest(page.content),
        "resource_page_bytes": len(page.content),
    })
    if page.status_code != 200 or not approved(page.url):
        report["blocker"] = "authoritative_resource_page_not_retrievable_on_approved_host"
    else:
        links = candidate_links(page.text)
        report["candidate_links"] = links
        for url in links:
            try:
                response = session.get(url, timeout=120, allow_redirects=True)
                if not approved(response.url):
                    report["attempts"].append({"url": url, "accepted": False, "reason": "redirected_off_approved_ogd_hosts", "final_url": response.url})
                    continue
                attempt = inspect_csv(response.content, response.headers.get("Content-Type", ""), response.url)
                attempt["status_code"] = response.status_code
                report["attempts"].append(attempt)
                if response.status_code == 200 and attempt.get("accepted"):
                    payload = output_dir / "hmis_jharkhand_2014_15_raw.csv"
                    payload.write_bytes(response.content)
                    report.update({
                        "raw_payload_acquired": True,
                        "raw_sha256": attempt["sha256"],
                        "raw_byte_count": attempt["byte_count"],
                        "raw_payload_url": response.url,
                        "raw_payload_file": payload.name,
                        "observed_schema": attempt["observed_columns"],
                        "authoritative_schema_fields_verified": attempt["authoritative_schema_fields_verified"],
                    })
                    break
            except requests.RequestException as exc:
                report["attempts"].append({"url": url, "accepted": False, "reason": f"{type(exc).__name__}: {exc}"})
        if not report["raw_payload_acquired"]:
            report["blocker"] = "no_explicit_authoritative_csv_payload_admitted_from_resource_page"

    (output_dir / "hmis_jharkhand_2014_15_acquisition.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=Path("build/health_hmis_jharkhand_2014_15"))
    args = parser.parse_args()
    print(json.dumps(run(args.output_dir), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
