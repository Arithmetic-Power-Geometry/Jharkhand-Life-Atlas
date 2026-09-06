from __future__ import annotations

import argparse
import hashlib
import re
import urllib.parse
import urllib.request
from pathlib import Path

import polars as pl

OFFICIAL_OGD_HOSTS = {"data.gov.in", "www.data.gov.in", "jk.data.gov.in"}
MISSING_TOKENS = {"", "na", "n/a", "null", "none", "-", "--", "not available"}


def _norm_text(value: object) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip()).casefold()


def _norm_name(value: object) -> str:
    text = re.sub(r"[^0-9a-zA-Z ]+", " ", str(value or ""))
    return re.sub(r"\s+", " ", text).strip().casefold()


def _parse_numeric(value: object) -> float | None:
    text = str(value or "").strip()
    if text.casefold() in MISSING_TOKENS:
        return None
    text = text.replace(",", "")
    try:
        return float(text)
    except ValueError as exc:
        raise ValueError(f"Non-numeric HMIS value cannot be published: {value!r}") from exc


def download_official_ogd(url: str, destination: Path, expected_sha256: str | None = None) -> str:
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" or parsed.hostname not in OFFICIAL_OGD_HOSTS:
        raise ValueError("HMIS acquisition is restricted to an explicit HTTPS data.gov.in host")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url, timeout=90) as response:  # nosec: allowlisted official hosts only
        payload = response.read()
    digest = hashlib.sha256(payload).hexdigest()
    if expected_sha256 and digest.casefold() != expected_sha256.casefold():
        raise ValueError(f"SHA-256 mismatch: expected {expected_sha256}, got {digest}")
    destination.write_bytes(payload)
    return digest


def census2011_district_index(core_places_csv: Path) -> dict[str, tuple[str, str]]:
    frame = pl.read_csv(core_places_csv, infer_schema_length=2000, ignore_errors=False)
    required = {"place_id", "place_type", "name", "district_code"}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"Core geography is missing required columns: {sorted(missing)}")
    rows = frame.filter(pl.col("place_type").cast(pl.String).str.to_lowercase() == "district").select(
        ["place_id", "name", "district_code"]
    )
    index: dict[str, tuple[str, str]] = {}
    for row in rows.iter_rows(named=True):
        key = _norm_name(row["name"])
        if not key:
            continue
        value = (str(row["place_id"]), str(row["district_code"]))
        if key in index and index[key] != value:
            raise ValueError(f"Ambiguous Census-2011 district name: {row['name']!r}")
        index[key] = value
    if not index:
        raise ValueError("No Census-2011 district records found in the core geography backbone")
    return index


def curate_hmis_district_csv(
    input_csv: Path,
    core_places_csv: Path,
    output_csv: Path,
    *,
    source_id: str,
    period: str,
    district_column: str,
    indicator_column: str,
    value_column: str,
    unit: str,
) -> dict[str, int]:
    if not period.strip():
        raise ValueError("An explicit HMIS reference period is required")
    frame = pl.read_csv(input_csv, infer_schema_length=5000, ignore_errors=False)
    required = {district_column, indicator_column, value_column}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"HMIS CSV missing explicitly configured columns: {sorted(missing)}")

    district_index = census2011_district_index(core_places_csv)
    output: list[dict[str, object]] = []
    unmatched: set[str] = set()

    for row in frame.iter_rows(named=True):
        district_raw = row[district_column]
        district_key = _norm_name(district_raw)
        if district_key not in district_index:
            unmatched.add(str(district_raw))
            continue
        indicator_raw = str(row[indicator_column] or "").strip()
        if not indicator_raw:
            continue
        place_id, district_code = district_index[district_key]
        output.append(
            {
                "place_id": place_id,
                "district_code": district_code,
                "source_geography_name": str(district_raw).strip(),
                "indicator_id": _norm_text(indicator_raw).replace(" ", "_"),
                "indicator_label": indicator_raw,
                "period": period,
                "value_numeric": _parse_numeric(row[value_column]),
                "unit": unit,
                "source_id": source_id,
                "observation_type": "observed_district_aggregate",
                "quality_class": "authoritative_source_exact_census2011_district_name_link",
                "geographic_link_method": "unique_exact_normalized_name_to_census2011_district",
            }
        )

    if unmatched:
        names = ", ".join(sorted(unmatched)[:20])
        raise ValueError(
            "HMIS district names failed exact Census-2011 linking; no fuzzy/current-geography fallback is allowed. "
            f"Unmatched examples: {names}"
        )
    if not output:
        raise ValueError("HMIS ingestion produced zero publishable rows")

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    pl.DataFrame(output).write_csv(output_csv)
    return {"input_rows": frame.height, "output_rows": len(output), "unmatched_districts": 0}


def main() -> None:
    parser = argparse.ArgumentParser(description="Fail-closed Jharkhand HMIS district ingestion")
    parser.add_argument("--input-csv", type=Path)
    parser.add_argument("--url")
    parser.add_argument("--expected-sha256")
    parser.add_argument("--core-places", type=Path, default=Path("data/curated/core_geography/census_places_2011.csv"))
    parser.add_argument("--output", type=Path, default=Path("data/curated/health_access/health_service_activity.csv"))
    parser.add_argument("--source-id", default="OGD_HMIS_JH_DISTRICT")
    parser.add_argument("--period", required=True)
    parser.add_argument("--district-column", required=True)
    parser.add_argument("--indicator-column", required=True)
    parser.add_argument("--value-column", required=True)
    parser.add_argument("--unit", default="count")
    args = parser.parse_args()

    input_csv = args.input_csv
    if args.url:
        input_csv = input_csv or Path("data/raw/health_access/hmis_source.csv")
        digest = download_official_ogd(args.url, input_csv, args.expected_sha256)
        print(f"download_sha256={digest}")
    if input_csv is None or not input_csv.exists():
        raise SystemExit("Provide --input-csv or an official --url")

    stats = curate_hmis_district_csv(
        input_csv,
        args.core_places,
        args.output,
        source_id=args.source_id,
        period=args.period,
        district_column=args.district_column,
        indicator_column=args.indicator_column,
        value_column=args.value_column,
        unit=args.unit,
    )
    print(stats)


if __name__ == "__main__":
    main()
