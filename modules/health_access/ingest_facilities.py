from __future__ import annotations

import argparse
import hashlib
import re
from pathlib import Path

import polars as pl


def _norm_name(value: object) -> str:
    text = re.sub(r"[^0-9a-zA-Z ]+", " ", str(value or ""))
    return re.sub(r"\s+", " ", text).strip().casefold()


def _clean_text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _parse_float(value: object, *, field: str) -> float | None:
    text = str(value or "").strip()
    if not text or text.casefold() in {"na", "n/a", "null", "none", "-", "--", "not available"}:
        return None
    try:
        return float(text)
    except ValueError as exc:
        raise ValueError(f"Non-numeric {field} cannot be published: {value!r}") from exc


def _facility_source_id(source_id: str, source_record_id: object) -> str:
    record = str(source_record_id or "").strip()
    if not record:
        raise ValueError("A source-provided facility record identifier is required; JLA will not invent cross-source identity")
    digest = hashlib.sha256(f"{source_id}|{record}".encode("utf-8")).hexdigest()[:20]
    return f"{source_id}:{digest}"


def census2011_district_index(core_places_csv: Path) -> dict[str, tuple[str, str]]:
    frame = pl.read_csv(core_places_csv, infer_schema_length=2000, ignore_errors=False)
    required = {"place_id", "place_type", "name", "district_code"}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"Core geography is missing required columns: {sorted(missing)}")
    districts = frame.filter(pl.col("place_type").cast(pl.String).str.to_lowercase() == "district").select(
        ["place_id", "name", "district_code"]
    )
    index: dict[str, tuple[str, str]] = {}
    for row in districts.iter_rows(named=True):
        key = _norm_name(row["name"])
        value = (str(row["place_id"]), str(row["district_code"]))
        if not key:
            continue
        if key in index and index[key] != value:
            raise ValueError(f"Ambiguous Census-2011 district name: {row['name']!r}")
        index[key] = value
    if not index:
        raise ValueError("No Census-2011 district records found in the core geography backbone")
    return index


def curate_facility_directory(
    input_csv: Path,
    core_places_csv: Path,
    output_csv: Path,
    *,
    source_id: str,
    reference_period: str,
    source_geography_vintage: str,
    state_column: str,
    district_column: str,
    record_id_column: str,
    name_column: str,
    type_column: str,
    ownership_column: str,
    address_column: str | None = None,
    latitude_column: str | None = None,
    longitude_column: str | None = None,
    systems_column: str | None = None,
) -> dict[str, int]:
    if not reference_period.strip():
        raise ValueError("An explicit facility-directory reference period is required")

    geography_vintage = source_geography_vintage.strip().casefold()
    if geography_vintage != "census2011_compatible":
        raise ValueError(
            "Facility source geography is not explicitly Census-2011 compatible; an evidence-backed temporal crosswalk "
            "is required before linking current or differently-vintaged district geography to the Census-2011 backbone"
        )

    frame = pl.read_csv(input_csv, infer_schema_length=10000, ignore_errors=False)
    required = {state_column, district_column, record_id_column, name_column, type_column, ownership_column}
    for optional in (address_column, latitude_column, longitude_column, systems_column):
        if optional:
            required.add(optional)
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"Facility CSV missing explicitly configured columns: {sorted(missing)}")

    district_index = census2011_district_index(core_places_csv)
    output: list[dict[str, object]] = []
    unmatched: set[str] = set()
    skipped_other_states = 0

    for row in frame.iter_rows(named=True):
        if _norm_name(row[state_column]) != "jharkhand":
            skipped_other_states += 1
            continue

        district_raw = row[district_column]
        district_key = _norm_name(district_raw)
        if district_key not in district_index:
            unmatched.add(str(district_raw))
            continue

        facility_name = _clean_text(row[name_column])
        facility_type = _clean_text(row[type_column])
        ownership = _clean_text(row[ownership_column])
        if not facility_name or not facility_type or not ownership:
            raise ValueError("Jharkhand facility row is missing name/type/ownership; publication aborted")

        latitude = _parse_float(row[latitude_column], field="latitude") if latitude_column else None
        longitude = _parse_float(row[longitude_column], field="longitude") if longitude_column else None
        if (latitude is None) != (longitude is None):
            raise ValueError("Facility coordinates must be both present or both missing")
        if latitude is not None and not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
            raise ValueError(f"Facility coordinate outside valid WGS84 bounds: {(latitude, longitude)}")

        place_id, district_code = district_index[district_key]
        output.append(
            {
                "facility_source_id": _facility_source_id(source_id, row[record_id_column]),
                "source_record_id": str(row[record_id_column]).strip(),
                "facility_name": facility_name,
                "facility_type": facility_type,
                "ownership": ownership,
                "place_id": place_id,
                "district_code": district_code,
                "source_district_name": str(district_raw).strip(),
                "latitude": latitude,
                "longitude": longitude,
                "address": _clean_text(row[address_column]) if address_column else None,
                "systems_of_medicine": _clean_text(row[systems_column]) if systems_column else None,
                "source_id": source_id,
                "reference_period": reference_period,
                "source_geography_vintage": source_geography_vintage.strip(),
                "observation_type": "observed_source_facility_record",
                "quality_class": "authoritative_source_exact_census2011_district_name_link",
                "geographic_link_method": "unique_exact_normalized_name_to_census2011_district",
            }
        )

    if unmatched:
        names = ", ".join(sorted(unmatched)[:20])
        raise ValueError(
            "Jharkhand facility district names failed exact Census-2011 linking; no fuzzy/current-geography fallback is allowed. "
            f"Unmatched examples: {names}"
        )
    if not output:
        raise ValueError("Facility ingestion produced zero publishable Jharkhand rows")

    ids = [str(row["facility_source_id"]) for row in output]
    if len(ids) != len(set(ids)):
        raise ValueError("Duplicate source facility identifiers detected; source identity must be unique")

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    pl.DataFrame(output).write_csv(output_csv)
    return {
        "input_rows": frame.height,
        "jharkhand_output_rows": len(output),
        "skipped_other_states": skipped_other_states,
        "unmatched_districts": 0,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Fail-closed official OGD health-facility directory ingestion")
    parser.add_argument("--input-csv", type=Path, required=True)
    parser.add_argument("--core-places", type=Path, default=Path("data/curated/core_geography/census_places_2011.csv"))
    parser.add_argument("--output", type=Path, default=Path("data/curated/health_access/health_facilities.csv"))
    parser.add_argument("--source-id", required=True)
    parser.add_argument("--reference-period", required=True)
    parser.add_argument(
        "--source-geography-vintage",
        required=True,
        help="Must be census2011_compatible for direct linking; other vintages require an evidence-backed crosswalk before ingestion.",
    )
    parser.add_argument("--state-column", required=True)
    parser.add_argument("--district-column", required=True)
    parser.add_argument("--record-id-column", required=True)
    parser.add_argument("--name-column", required=True)
    parser.add_argument("--type-column", required=True)
    parser.add_argument("--ownership-column", required=True)
    parser.add_argument("--address-column")
    parser.add_argument("--latitude-column")
    parser.add_argument("--longitude-column")
    parser.add_argument("--systems-column")
    args = parser.parse_args()

    stats = curate_facility_directory(
        args.input_csv,
        args.core_places,
        args.output,
        source_id=args.source_id,
        reference_period=args.reference_period,
        source_geography_vintage=args.source_geography_vintage,
        state_column=args.state_column,
        district_column=args.district_column,
        record_id_column=args.record_id_column,
        name_column=args.name_column,
        type_column=args.type_column,
        ownership_column=args.ownership_column,
        address_column=args.address_column,
        latitude_column=args.latitude_column,
        longitude_column=args.longitude_column,
        systems_column=args.systems_column,
    )
    print(stats)


if __name__ == "__main__":
    main()
