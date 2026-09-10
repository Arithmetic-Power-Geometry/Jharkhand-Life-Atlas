"""Resolve Health OGD payload identities from explicit official evidence only.

This resolver deliberately does *not* construct resource UUIDs or download URLs
from titles/slugs. It inspects the verified official OGD catalog API control,
the catalog's resource-list view, and canonical resource pages. It accepts either
(1) an explicit machine-resource UUID tied to the target in authoritative content,
or (2) an explicit downloadable data URL observed on that target's canonical
official page. Results remain unpublished acquisition evidence until bytes are
separately acquired, hashed, schema-inspected and validated.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import requests

CATALOG_API_CONTROL = "https://www.data.gov.in/apis/e48a8bcf-ff56-4f39-839d-095827ba2a18"
CATALOG_PAGE = "https://www.data.gov.in/catalog/hospital-directory-national-health-portal"
CATALOG_RESOURCE_LIST = (
    "https://www.data.gov.in/catalog/hospital-directory-national-health-portal"
    "?filters%5Bfield_catalog_reference%5D=323881&format=json&limit=6&offset=0"
    "&sort%5Bcreated%5D=desc"
)
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0 Safari/537.36"
UUID_RE = re.compile(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}\b")
RESOURCE_URL_UUID_RE = re.compile(
    r"(?:api\.data\.gov\.in/resource/|data\.gov\.in/(?:resource|resources)/)([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12})",
    re.IGNORECASE,
)
URL_RE = re.compile(r"https?://[^\s\"'<>]+", re.IGNORECASE)
DATA_SUFFIXES = (".csv", ".xls", ".xlsx", ".zip", ".json", ".geojson")
CATALOG_ID = "e48a8bcf-ff56-4f39-839d-095827ba2a18"

TARGETS = {
    "OGD_NIN_HEALTH_FACILITIES_GEO_2026": {
        "title": "NIN Health Faclities with Geo Code and additional parameters (updated till last month)",
        "slug": "nin-health-faclities-geo-code-and-additional-parameters-updated-till-last-month",
        "resource_urls": [
            "https://www.data.gov.in/resource/nin-health-faclities-geo-code-and-additional-parameters-updated-till-last-month",
            "https://data.gov.in/resources/nin-health-faclities-geo-code-and-additional-parameters-updated-till-last-month",
        ],
    },
    "OGD_NHP_HOSPITAL_GEO_2026": {
        "title": "National Hospital Directory with Geo Code and additional parameters (updated till last month)",
        "slug": "national-hospital-directory-geo-code-and-additional-parameters-updated-till-last-month",
        "resource_urls": [
            "https://www.data.gov.in/resource/national-hospital-directory-geo-code-and-additional-parameters-updated-till-last-month",
            "https://data.gov.in/resource/national-hospital-directory-geo-code-and-additional-parameters-updated-till-last-month",
        ],
    },
}


def _fetch(session: requests.Session, url: str) -> dict[str, Any]:
    record: dict[str, Any] = {"requested_url": url}
    try:
        r = session.get(url, timeout=90, allow_redirects=True)
        record.update({
            "status_code": r.status_code,
            "final_url": r.url,
            "content_type": r.headers.get("Content-Type", ""),
            "byte_count": len(r.content),
            "sha256": hashlib.sha256(r.content).hexdigest(),
        })
        if r.status_code == 200 and r.content:
            record["text"] = r.text
    except requests.RequestException as exc:
        record["error"] = f"{type(exc).__name__}: {exc}"
    return record


def _uuid_contexts(text: str) -> list[dict[str, str]]:
    contexts: list[dict[str, str]] = []
    for match in UUID_RE.finditer(text):
        start = max(0, match.start() - 500)
        end = min(len(text), match.end() + 500)
        contexts.append({"uuid": match.group(0).lower(), "context": text[start:end]})
    return contexts


def _explicit_resource_url_uuids(text: str) -> list[str]:
    return sorted({m.group(1).lower() for m in RESOURCE_URL_UUID_RE.finditer(text) if m.group(1).lower() != CATALOG_ID})


def _is_official_data_host(host: str) -> bool:
    h = host.casefold().split(":", 1)[0]
    return h in {"data.gov.in", "www.data.gov.in", "api.data.gov.in"} or h.endswith(".data.gov.in")


def _explicit_official_payload_urls(text: str) -> list[str]:
    """Return only literal official data URLs that look like downloadable payloads.

    This is intentionally conservative. Relative links, JavaScript-generated URLs,
    title-derived paths and third-party mirrors are not promoted. HTML entities are
    decoded only after a literal absolute URL has been observed in authoritative
    content.
    """
    found: set[str] = set()
    decoded = html.unescape(text).replace("\\/", "/")
    for match in URL_RE.finditer(decoded):
        url = match.group(0).rstrip(".,);]}")
        parsed = urlparse(url)
        if not _is_official_data_host(parsed.netloc):
            continue
        lower_path = parsed.path.casefold()
        lower_query = parsed.query.casefold()
        explicit_file = lower_path.endswith(DATA_SUFFIXES)
        explicit_api = parsed.netloc.casefold() == "api.data.gov.in" and "/resource/" in lower_path
        explicit_export = "format=csv" in lower_query or "format=json" in lower_query
        if explicit_file or explicit_api or explicit_export:
            found.add(url)
    return sorted(found)


def _is_tied_to_target(context: str, target: dict[str, Any]) -> bool:
    c = context.casefold()
    slug = target["slug"].casefold()
    title_tokens = [t for t in re.split(r"[^a-z0-9]+", target["title"].casefold()) if len(t) >= 5]
    return slug in c or sum(token in c for token in title_tokens) >= max(4, len(title_tokens) // 2)


def _is_target_page(page: dict[str, Any], target: dict[str, Any]) -> bool:
    requested = str(page.get("requested_url", "")).rstrip("/").casefold()
    final = str(page.get("final_url", "")).rstrip("/").casefold()
    target_urls = {str(u).rstrip("/").casefold() for u in target["resource_urls"]}
    return requested in target_urls or final in target_urls


def resolve(output_dir: Path) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    session.headers.update({"User-Agent": USER_AGENT, "Accept-Language": "en-US,en;q=0.9"})

    fetched: list[dict[str, Any]] = []
    for url in [CATALOG_PAGE, CATALOG_RESOURCE_LIST, CATALOG_API_CONTROL]:
        fetched.append(_fetch(session, url))
    for target in TARGETS.values():
        for url in target["resource_urls"]:
            fetched.append(_fetch(session, url))

    results: dict[str, Any] = {}
    for source_id, target in TARGETS.items():
        candidates: dict[str, list[dict[str, str]]] = {}
        direct_payloads: dict[str, list[dict[str, str]]] = {}
        for page in fetched:
            text = page.get("text")
            if not text:
                continue

            # Strong evidence path: explicit machine resource URL or explicit
            # official downloadable data URL on the canonical page for this target.
            if _is_target_page(page, target):
                evidence_url = page.get("final_url", page["requested_url"])
                for resource_id in _explicit_resource_url_uuids(text):
                    candidates.setdefault(resource_id, []).append({
                        "evidence_url": evidence_url,
                        "evidence_type": "explicit_machine_resource_url_on_canonical_target_page",
                        "context": f"authoritative canonical target page explicitly contains machine resource URL for {resource_id}",
                    })
                for payload_url in _explicit_official_payload_urls(text):
                    direct_payloads.setdefault(payload_url, []).append({
                        "evidence_url": evidence_url,
                        "evidence_type": "explicit_official_payload_url_on_canonical_target_page",
                        "context": "authoritative canonical target page explicitly contains this downloadable/API data URL",
                    })

            # Secondary UUID evidence path: UUID appears in authoritative content
            # with strong local title/slug context. Multiple candidates fail closed.
            for item in _uuid_contexts(text):
                if item["uuid"] == CATALOG_ID:
                    continue
                if _is_tied_to_target(item["context"], target):
                    candidates.setdefault(item["uuid"], []).append({
                        "evidence_url": page.get("final_url", page["requested_url"]),
                        "evidence_type": "uuid_with_strong_local_target_context",
                        "context": item["context"],
                    })

        if len(candidates) == 1:
            resource_id, evidence = next(iter(candidates.items()))
            results[source_id] = {
                "status": "resolved_from_explicit_authoritative_evidence",
                "machine_resource_id": resource_id,
                "machine_api_url": f"https://api.data.gov.in/resource/{resource_id}",
                "direct_payload_url": None,
                "identity_evidence": evidence,
                "raw_payload_acquired": False,
                "schema_inspected": False,
                "publication_allowed": False,
            }
        elif not candidates and len(direct_payloads) == 1:
            payload_url, evidence = next(iter(direct_payloads.items()))
            results[source_id] = {
                "status": "resolved_direct_payload_url_from_explicit_authoritative_evidence",
                "machine_resource_id": None,
                "machine_api_url": None,
                "direct_payload_url": payload_url,
                "identity_evidence": evidence,
                "raw_payload_acquired": False,
                "schema_inspected": False,
                "publication_allowed": False,
            }
        else:
            results[source_id] = {
                "status": (
                    "unresolved"
                    if not candidates and not direct_payloads
                    else "ambiguous_multiple_explicit_candidates"
                ),
                "machine_resource_id": None,
                "candidate_ids": sorted(candidates),
                "candidate_direct_payload_urls": sorted(direct_payloads),
                "raw_payload_acquired": False,
                "schema_inspected": False,
                "publication_allowed": False,
            }

    public_fetch = [{k: v for k, v in page.items() if k != "text"} for page in fetched]
    report = {
        "contract": "JLA_OGD_RESOURCE_IDENTITY_RESOLUTION_V2",
        "resolved_at_utc": datetime.now(timezone.utc).isoformat(),
        "catalog_api_control": CATALOG_API_CONTROL,
        "catalog_resource_list": CATALOG_RESOURCE_LIST,
        "rules": [
            "never_construct_resource_uuid_from_title_or_slug",
            "never_construct_download_url_from_title_or_slug",
            "accept_only_explicit_identifier_tied_to_target_in_authoritative_content",
            "accept_only_explicit_official_payload_url_observed_on_canonical_target_page",
            "canonical_target_page_may_supply_explicit_machine_resource_url_evidence",
            "catalog_api_identifier_is_not_resource_identifier",
            "identity_resolution_does_not_mean_payload_acquisition_or_publication",
        ],
        "fetches": public_fetch,
        "resources": results,
    }
    (output_dir / "hospital_resource_identity_resolution.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, default=Path("build/health_resource_identity"))
    args = parser.parse_args()
    print(json.dumps(resolve(args.output_dir), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
