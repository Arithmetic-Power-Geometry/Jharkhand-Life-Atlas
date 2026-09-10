"""Resolve Health OGD machine-resource identities from explicit official evidence only.

This resolver deliberately does *not* construct resource UUIDs from titles/slugs.
It inspects the verified official OGD catalog API control, the catalog's own
resource-list view, and canonical resource pages and accepts a UUID only when the
same explicit identifier is tied to the registered resource by authoritative page
content/hyperlinks. Results remain unpublished acquisition evidence until raw bytes
are separately acquired, hashed, schema-inspected and validated.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

CATALOG_API_CONTROL = "https://www.data.gov.in/apis/e48a8bcf-ff56-4f39-839d-095827ba2a18"
CATALOG_PAGE = "https://www.data.gov.in/catalog/hospital-directory-national-health-portal"
# Exact resource-list view exposed by the official OGD catalog. This is evidence to
# inspect, not a template from which a resource UUID may be constructed.
CATALOG_RESOURCE_LIST = (
    "https://www.data.gov.in/catalog/hospital-directory-national-health-portal"
    "?filters%5Bfield_catalog_reference%5D=323881&format=json&limit=6&offset=0"
    "&sort%5Bcreated%5D=desc"
)
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0 Safari/537.36"
UUID_RE = re.compile(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}\b")

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
        start = max(0, match.start() - 300)
        end = min(len(text), match.end() + 300)
        contexts.append({"uuid": match.group(0).lower(), "context": text[start:end]})
    return contexts


def _is_tied_to_target(context: str, target: dict[str, Any]) -> bool:
    c = context.casefold()
    slug = target["slug"].casefold()
    title_tokens = [t for t in re.split(r"[^a-z0-9]+", target["title"].casefold()) if len(t) >= 5]
    # Require strong explicit target evidence in the same local authoritative context.
    return slug in c or sum(token in c for token in title_tokens) >= max(4, len(title_tokens) // 2)


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
        for page in fetched:
            text = page.get("text")
            if not text:
                continue
            for item in _uuid_contexts(text):
                if item["uuid"] == "e48a8bcf-ff56-4f39-839d-095827ba2a18":
                    # Verified catalog API identity; explicitly not a resource UUID.
                    continue
                if _is_tied_to_target(item["context"], target):
                    candidates.setdefault(item["uuid"], []).append({
                        "evidence_url": page.get("final_url", page["requested_url"]),
                        "context": item["context"],
                    })
        if len(candidates) == 1:
            resource_id, evidence = next(iter(candidates.items()))
            results[source_id] = {
                "status": "resolved_from_explicit_authoritative_evidence",
                "machine_resource_id": resource_id,
                "machine_api_url": f"https://api.data.gov.in/resource/{resource_id}",
                "identity_evidence": evidence,
                "raw_payload_acquired": False,
                "schema_inspected": False,
                "publication_allowed": False,
            }
        else:
            results[source_id] = {
                "status": "unresolved" if not candidates else "ambiguous_multiple_explicit_candidates",
                "machine_resource_id": None,
                "candidate_ids": sorted(candidates),
                "raw_payload_acquired": False,
                "schema_inspected": False,
                "publication_allowed": False,
            }

    public_fetch = []
    for page in fetched:
        public_fetch.append({k: v for k, v in page.items() if k != "text"})

    report = {
        "contract": "JLA_OGD_RESOURCE_IDENTITY_RESOLUTION_V1",
        "resolved_at_utc": datetime.now(timezone.utc).isoformat(),
        "catalog_api_control": CATALOG_API_CONTROL,
        "catalog_resource_list": CATALOG_RESOURCE_LIST,
        "rules": [
            "never_construct_resource_uuid_from_title_or_slug",
            "accept_only_explicit_identifier_tied_to_target_in_authoritative_content",
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
