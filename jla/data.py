from __future__ import annotations
from pathlib import Path
import csv, io, zipfile
try:
    import polars as pl
except Exception:
    pl = None
from .paths import DATA_DIR, REGISTRY_DIR

CORE_DIR = DATA_DIR / "curated" / "core_geography"

CORE_RESEARCH_TABLES = [
    "census_places_2011.csv",
    "village_demography_2011.csv",
    "village_amenities_2011.csv",
    "census_mdds_crosswalk_2001_2011.csv",
    "census_lgd_temporal_crosswalk.csv",
    "lgd_districts_current.csv",
    "lgd_subdistricts_current.csv",
    "lgd_blocks_current.csv",
    "lgd_panchayats_current.csv",
    "lgd_villages_current.csv",
    "pca_source_manifest_2011.csv",
    "source_coverage.csv",
    "current_administration.csv",
]

def read_csv(path: Path):
    if pl is None:
        with path.open(encoding="utf-8", newline="") as f:
            return list(csv.DictReader(f))
    return pl.read_csv(path, infer_schema_length=10000, null_values=["", "NA", "N/A", "null"])

def places():
    return read_csv(CORE_DIR / "places.csv")

def current_administration():
    return read_csv(CORE_DIR / "current_administration.csv")

def source_coverage():
    return read_csv(CORE_DIR / "source_coverage.csv")

def optional_core_table(name: str):
    p = CORE_DIR / name
    return read_csv(p) if p.exists() else None

def core_research_tables() -> list[str]:
    return [name for name in CORE_RESEARCH_TABLES if (CORE_DIR / name).exists()]

def sources():
    return read_csv(REGISTRY_DIR / "sources.csv")

def variables():
    return read_csv(REGISTRY_DIR / "variables.csv")

def module_indicators(module_path: str):
    p = Path(module_path) / "data" / "indicators.csv"
    return read_csv(p) if p.exists() else None

def dataframe_to_csv_bytes(df) -> bytes:
    if pl is not None and isinstance(df, pl.DataFrame):
        return df.write_csv().encode("utf-8")
    if not df:
        return b""
    out=io.StringIO()
    w=csv.DictWriter(out, fieldnames=list(df[0].keys()))
    w.writeheader(); w.writerows(df)
    return out.getvalue().encode()

def research_bundle(data_df, source_df, variable_df, name="JLA_extract") -> bytes:
    mem=io.BytesIO()
    with zipfile.ZipFile(mem, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("data.csv", dataframe_to_csv_bytes(data_df))
        z.writestr("sources.csv", dataframe_to_csv_bytes(source_df))
        z.writestr("data_dictionary.csv", dataframe_to_csv_bytes(variable_df))
        for filename in core_research_tables():
            z.writestr(f"core_geography/{filename}", (CORE_DIR / filename).read_bytes())
        z.writestr(
            "README.txt",
            "Jharkhand Life Atlas research extract. Cite JLA and each underlying source listed in sources.csv. "
            "Missing values are not zero. Census-2011 and current administrative layers are intentionally kept distinct. "
            "The core_geography folder contains the verified Census baseline, DCHB village amenities, MDDS 2001-2011 crosswalk, "
            "current LGD layers and the conservative Census-2011-to-LGD temporal crosswalk. Unmatched temporal links remain explicit.\n",
        )
        z.writestr("LICENSE.txt", "JLA original material: CC BY 4.0. Third-party source rights remain with their respective providers.\n")
    return mem.getvalue()
