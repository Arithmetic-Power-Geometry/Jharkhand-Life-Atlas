from __future__ import annotations

import argparse
from pathlib import Path

import polars as pl

REQUIRED_COLUMNS = {
    "source_geography_vintage",
    "source_district_name",
    "source_district_code",
    "census2011_district_code",
    "relationship",
    "evidence_source_id",
    "evidence_url",
    "evidence_reference_date",
    "reviewed_on",
    "review_status",
    "notes",
}


def validate_crosswalk(crosswalk_csv: Path, core_places_csv: Path, *, source_geography_vintage: str) -> dict[str, int]:
    vintage = source_geography_vintage.strip()
    if not vintage or vintage.casefold() == "census2011_compatible":
        raise ValueError("Crosswalk validation is only for an explicit non-Census-2011 source geography vintage")

    crosswalk = pl.read_csv(crosswalk_csv, infer_schema_length=5000, ignore_errors=False, null_values=[""])
    missing = REQUIRED_COLUMNS.difference(crosswalk.columns)
    if missing:
        raise ValueError(f"Health geography crosswalk missing required columns: {sorted(missing)}")
    if crosswalk.height == 0:
        raise ValueError("Health geography crosswalk is empty")

    core = pl.read_csv(core_places_csv, infer_schema_length=5000, ignore_errors=False)
    needed_core = {"place_type", "district_code"}
    missing_core = needed_core.difference(core.columns)
    if missing_core:
        raise ValueError(f"Core geography missing required columns: {sorted(missing_core)}")
    census_codes = {
        str(v).strip()
        for v in core.filter(pl.col("place_type").cast(pl.String).str.to_lowercase() == "district")["district_code"].to_list()
        if v is not None and str(v).strip()
    }
    if not census_codes:
        raise ValueError("No Census-2011 district codes found in the core geography backbone")

    seen: set[tuple[str, str]] = set()
    verified = 0
    for row in crosswalk.iter_rows(named=True):
        row_vintage = str(row["source_geography_vintage"] or "").strip()
        if row_vintage != vintage:
            raise ValueError("Crosswalk contains a row from a different source geography vintage")

        source_name = str(row["source_district_name"] or "").strip()
        if not source_name:
            raise ValueError("Crosswalk source_district_name must not be blank")
        source_code = None if row["source_district_code"] is None else str(row["source_district_code"]).strip() or None
        identity = (source_code or "<NULL>", source_name.casefold())
        if identity in seen:
            raise ValueError(f"Crosswalk source district does not resolve uniquely: {source_name!r}")
        seen.add(identity)

        relationship = str(row["relationship"] or "").strip()
        review_status = str(row["review_status"] or "").strip()
        if relationship != "equivalent" or review_status != "verified_equivalent":
            raise ValueError(
                "Publication crosswalk may contain only relationship=equivalent and review_status=verified_equivalent; "
                "split/merge/boundary-change/unresolved geography must remain unpublished"
            )

        target = str(row["census2011_district_code"] or "").strip()
        if target not in census_codes:
            raise ValueError(f"Crosswalk target is not a Census-2011 Jharkhand district code: {target!r}")

        evidence_source = str(row["evidence_source_id"] or "").strip()
        evidence_url = str(row["evidence_url"] or "").strip()
        evidence_date = str(row["evidence_reference_date"] or "").strip()
        reviewed_on = str(row["reviewed_on"] or "").strip()
        if not evidence_source or not evidence_url.startswith("https://") or not evidence_date or not reviewed_on:
            raise ValueError("Every verified crosswalk row requires authoritative evidence source, HTTPS URL, reference date, and review date")
        verified += 1

    return {"rows": crosswalk.height, "verified_equivalent_rows": verified, "unique_source_districts": len(seen)}


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate an evidence-backed health district temporal crosswalk")
    parser.add_argument("--crosswalk", type=Path, required=True)
    parser.add_argument("--core-places", type=Path, default=Path("data/curated/core_geography/census_places_2011.csv"))
    parser.add_argument("--source-geography-vintage", required=True)
    args = parser.parse_args()
    print(validate_crosswalk(args.crosswalk, args.core_places, source_geography_vintage=args.source_geography_vintage))


if __name__ == "__main__":
    main()
