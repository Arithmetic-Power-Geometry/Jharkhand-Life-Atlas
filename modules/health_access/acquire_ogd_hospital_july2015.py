"""Acquire the explicit OGD Hospital Directory July-2015 resource without guessing IDs.

The script starts from the authoritative resource page discovered at data.gov.in,
extracts only explicit official download/API links, follows only approved OGD hosts,
and admits a payload only when its bytes are non-HTML and plausibly tabular/JSON.
Every accepted payload is hashed and its observed schema is recorded. If the
resource page does not expose a machine payload, the run ends successfully with a
machine-readable blocker; publication remains closed.
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

RESOURCE_PAGE = "https://www.data.gov.in/resource/hospital-directory-july-2015"
SOURCE_ID = "OGD_NHP_HOSPITAL_JULY_2015"
ALLOWED_HOSTS = {"data.gov.in", "www.data.gov.in", "api.data.gov.in"}
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/140 Safari/537.36"
HREF_RE = re.compile(r"(?:href|src)\s*=\s*[\"']([^\"']+)[\"']", re.I)
URL_RE = re.compile(r"https?://[^\s\"'<>]+", re.I)


def sha256(data: bytes) -> str:
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
        if not approved(url):
            continue
        low = url.casefold()
        # Accept only explicit official machine/data-looking links. The resource
        # page itself is excluded so an HTML page can never be mistaken for data.
        if url.rstrip("/") == RESOURCE_PAGE.rstrip("/"):
            continue
        if any(token in low for token in ("api.data.gov.in/resource/", ".csv", ".xls", ".xlsx", ".zip", "download", "/files/", "format=csv", "format=json")):
            out.add(url)
    return sorted(out)


def inspect_payload(data: bytes, content_type: str, url: str) -> dict:
    result = {"url": url, "byte_count": len(data), "sha256": sha256(data), "content_type": content_type}
    prefix = data[:512].lstrip().lower()
    if prefix.startswith(b"<!doctype html") or prefix.startswith(b"<html") or "text/html" in content_type.casefold():
        result.update({"accepted": False, "reason": "html_not_data"})
        return result

    low_url = url.casefold()
    if "json" in content_type.casefold() or low_url.endswith(".json") or prefix.startswith((b"{", b"[")):
        try:
            obj = json.loads(data.decode("utf-8-sig"))
            if isinstance(obj, dict):
                records = obj.get("records")
                if isinstance(records, list) and records and isinstance(records[0], dict):
                    result["observed_columns"] = list(records[0].keys())
                    result["observed_record_count"] = len(records)
                else:
                    result["observed_top_level_keys"] = list(obj.keys())[:100]
            elif isinstance(obj, list):
                result["observed_record_count"] = len(obj)
                if obj and isinstance(obj[0], dict):
                    result["observed_columns"] = list(obj[0].keys())
            result.update({"accepted": True, "format": "json"})
            return result
        except Exception as exc:
            result["json_parse_error"] = f"{type(exc).__name__}: {exc}"

    if "csv" in content_type.casefold() or ".csv" in low_url:
        try:
            text = data.decode("utf-8-sig", errors="strict")
            reader = csv.reader(io.StringIO(text))
            header = next(reader)
            result.update({"accepted": True, "format": "csv", "observed_columns": header})
            return result
        except Exception as exc:
            result["csv_parse_error"] = f"{type(exc).__name__}: {exc}"

    if data[:2] == b"PK" and any(x in low_url for x in (".xlsx", ".zip", "download")):
        result.update({"accepted": True, "format": "zip_or_xlsx_container", "observed_columns": None})
        return result
    if data[:8] == bytes.fromhex("D0CF11E0A1B11AE1"):
        result.update({"accepted": True, "format": "xls_ole_container", "observed_columns": None})
        return result

    result.update({"accepted": False, "reason": "unrecognized_non_html_payload"})
    return result


def run(output_dir: Path) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT, "Accept-Language": "en-US,en;q=0.9"})

    page = session.get(RESOURCE_PAGE, timeout=90, allow_redirects=True)
    page_bytes = page.content
    report = {
        "contract": "JLA_HEALTH_OFFICIAL_PAYLOAD_ACQUISITION_V1",
        "source_id": SOURCE_ID,
        "resource_page": RESOURCE_PAGE,
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
        "resource_page_status": page.status_code,
        "resource_page_final_url": page.url,
        "resource_page_sha256": sha256(page_bytes),
        "resource_page_bytes": len(page_bytes),
        "candidate_links": [],
        "attempts": [],
        "raw_payload_acquired": False,
        "raw_sha256": None,
        "observed_schema": None,
        "publication_allowed": False,
        "rules": [
            "official_ogd_hosts_only",
            "never_guess_resource_uuid_or_download_url",
            "html_is_not_data",
            "hash_before_curation",
            "preserve_missing_as_null",
            "publication_requires_separate_geography_and_validation_gates",
        ],
    }

    if page.status_code != 200:
        report["blocker"] = "authoritative_resource_page_not_retrievable"
    else:
        links = candidate_links(page.text)
        report["candidate_links"] = links
        for url in links:
            try:
                response = session.get(url, timeout=120, allow_redirects=True)
                final_url = response.url
                if not approved(final_url):
                    report["attempts"].append({"url": url, "accepted": False, "reason": "redirected_off_approved_ogd_hosts", "final_url": final_url})
                    continue
                attempt = inspect_payload(response.content, response.headers.get("Content-Type", ""), final_url)
                attempt["status_code"] = response.status_code
                report["attempts"].append(attempt)
                if response.status_code == 200 and attempt.get("accepted"):
                    ext = {"csv": ".csv", "json": ".json", "xls_ole_container": ".xls", "zip_or_xlsx_container": ".bin"}.get(attempt.get("format"), ".bin")
                    payload_path = output_dir / f"hospital_directory_july2015_raw{ext}"
                    payload_path.write_bytes(response.content)
                    report["raw_payload_acquired"] = True
                    report["raw_sha256"] = attempt["sha256"]
                    report["raw_byte_count"] = attempt["byte_count"]
                    report["raw_payload_url"] = final_url
                    report["raw_payload_file"] = payload_path.name
                    report["observed_schema"] = attempt.get("observed_columns")
                    report["observed_format"] = attempt.get("format")
                    break
            except requests.RequestException as exc:
                report["attempts"].append({"url": url, "accepted": False, "reason": f"{type(exc).__name__}: {exc}"})

        if not report["raw_payload_acquired"]:
            report["blocker"] = "no_explicit_authoritative_machine_payload_admitted_from_resource_page"

    (output_dir / "hospital_directory_july2015_acquisition.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=Path("build/health_hospital_july2015"))
    args = parser.parse_args()
    print(json.dumps(run(args.output_dir), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
