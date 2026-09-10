"""Acquire the official OGD UDISE+ 2023-24 state infrastructure CSV.

Fail-closed: discover the download only from the authoritative resource page,
accept only Government OGD HTTPS payloads, hash immutable bytes, inspect observed
schema, and extract only the explicit Jharkhand aggregate row. No school-, staff-
or student-level records are handled here.
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
from urllib.parse import urljoin, urlparse

import requests

SOURCE_ID = "OGD_UDISE_INFRASTRUCTURE_2023_24_STATE"
RESOURCE_PAGE = "https://www.data.gov.in/resource/stateuts-wise-number-school-infrastructure-highlights-udise-data-during-2023-24"
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0 Safari/537.36"


def norm(v: object) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(v or "").strip().casefold()).strip("_")


def official(url: str) -> bool:
    h = (urlparse(url).hostname or "").casefold()
    return urlparse(url).scheme == "https" and (h == "data.gov.in" or h.endswith(".data.gov.in"))


class Links(HTMLParser):
    def __init__(self) -> None:
        super().__init__(); self.hrefs: list[str] = []
    def handle_starttag(self, tag, attrs):
        if tag.casefold() == "a":
            for k, v in attrs:
                if k.casefold() == "href" and v: self.hrefs.append(v)


def candidates(html: str) -> list[str]:
    p = Links(); p.feed(html); out = []
    for href in p.hrefs:
        u = urljoin(RESOURCE_PAGE, href)
        low = u.casefold()
        if official(u) and (".csv" in low or "download" in low or "datafile" in low):
            if u not in out: out.append(u)
    return out


def parse_csv(data: bytes):
    text = data.decode("utf-8-sig", errors="strict")
    try: dialect = csv.Sniffer().sniff(text[:8192], delimiters=",;\t|")
    except csv.Error: dialect = csv.excel
    r = csv.DictReader(io.StringIO(text), dialect=dialect)
    fields = [str(x).strip() for x in (r.fieldnames or [])]
    rows = [{str(k).strip(): (v if v != "" else None) for k, v in row.items()} for row in r]
    if len(fields) < 3 or not rows: raise RuntimeError("implausible UDISE CSV")
    return fields, rows


def acquire(out: Path):
    out.mkdir(parents=True, exist_ok=True)
    s = requests.Session(); s.headers.update({"User-Agent": USER_AGENT, "Accept-Language": "en-US,en;q=0.9"})
    attempts = []
    page = s.get(RESOURCE_PAGE, timeout=90, allow_redirects=True)
    attempts.append({"stage":"resource_page","status_code":page.status_code,"final_url":page.url,"bytes":len(page.content)})
    page.raise_for_status()
    if not official(page.url): raise RuntimeError("resource page redirected outside OGD")
    links = candidates(page.text)
    if not links: raise RuntimeError("no authoritative CSV/download link exposed; refusing to infer URL")
    payload = None; final = None
    for u in links:
        try:
            r = s.get(u, headers={"Referer":RESOURCE_PAGE,"Accept":"text/csv,application/csv,application/octet-stream,*/*;q=0.5"}, timeout=120, allow_redirects=True)
            attempts.append({"stage":"asset","requested_url":u,"status_code":r.status_code,"final_url":r.url,"bytes":len(r.content),"content_type":r.headers.get("Content-Type","")})
            prefix = r.content[:512].lstrip().lower()
            if r.status_code == 200 and r.content and official(r.url) and not prefix.startswith((b"<html", b"<!doctype html")):
                payload = r.content; final = r.url; break
        except requests.RequestException as exc:
            attempts.append({"stage":"asset","requested_url":u,"error":f"{type(exc).__name__}: {exc}"})
    if payload is None: raise RuntimeError("authoritative UDISE CSV acquisition failed; no mirror accepted: "+json.dumps(attempts))
    fields, rows = parse_csv(payload)
    state_cols = [f for f in fields if norm(f) in {"india_state_ut","state_ut","state","state_name"} or ("state" in norm(f) and "code" not in norm(f))]
    if len(state_cols) != 1: raise RuntimeError(f"cannot uniquely identify State/UT column: {fields}")
    state_col = state_cols[0]
    jh = [r for r in rows if norm(r.get(state_col)) == "jharkhand"]
    if len(jh) != 1: raise RuntimeError(f"expected one Jharkhand row, got {len(jh)}")
    sha = hashlib.sha256(payload).hexdigest()
    raw = out / "udise_infrastructure_2023_24.csv"; raw.write_bytes(payload)
    schema = {"contract":"JLA_OBSERVED_SCHEMA_V1","source_id":SOURCE_ID,"observed_fields":fields,"row_count":len(rows),"state_column":state_col,"jharkhand_rows":1,"missing_cells":sum(v is None for r in rows for v in r.values())}
    (out/"udise_observed_schema.json").write_text(json.dumps(schema,indent=2,ensure_ascii=False),encoding="utf-8")
    (out/"udise_jharkhand_state_infrastructure.json").write_text(json.dumps(jh[0],indent=2,ensure_ascii=False),encoding="utf-8")
    receipt = {"contract":"JLA_SOURCE_SNAPSHOT_V1","source_id":SOURCE_ID,"authority":"Ministry of Education, Department of School Education & Literacy / OGD India","resource_page":RESOURCE_PAGE,"final_official_payload_url":final,"academic_year":"2023-24","retrieved_at_utc":datetime.now(timezone.utc).isoformat(),"byte_count":len(payload),"sha256":sha,"raw_filename":raw.name,"observed_schema_file":"udise_observed_schema.json","rights":{"license":"Government Open Data License - India","attribution_required":True,"publication_allowed_after_validation":True},"geography":{"source_granularity":"state_ut","lower_geography_disaggregation_allowed":False},"null_semantics":"source blanks retained as null; never converted to zero","sensitive_person_level_data":False,"publication_allowed":False,"publication_blocker":"validate observed semantics and aggregate-only scope before curated publication","acquisition_attempts":attempts}
    (out/"udise_acquisition_receipt.json").write_text(json.dumps(receipt,indent=2,ensure_ascii=False),encoding="utf-8")
    return receipt


def main():
    p=argparse.ArgumentParser(); p.add_argument("--output-dir",type=Path,default=Path("build/education_udise")); a=p.parse_args(); print(json.dumps(acquire(a.output_dir),indent=2,ensure_ascii=False))

if __name__ == "__main__": main()
