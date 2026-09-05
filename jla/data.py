from __future__ import annotations
from pathlib import Path
import csv, io, zipfile
try:
    import polars as pl
except Exception:
    pl = None
from .paths import DATA_DIR, REGISTRY_DIR

CORE_DIR = DATA_DIR / "curated" / "core_geography"

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
        coverage = CORE_DIR / "source_coverage.csv"
        if coverage.exists(): z.writestr("source_coverage.csv", coverage.read_bytes())
        current = CORE_DIR / "current_administration.csv"
        if current.exists(): z.writestr("current_administration.csv", current.read_bytes())
        z.writestr("README.txt", "Jharkhand Life Atlas research extract. Cite JLA and each underlying source listed in sources.csv. Missing values are not zero. Census-2011 and current administrative layers are intentionally kept distinct.\n")
        z.writestr("LICENSE.txt", "JLA original material: CC BY 4.0. Third-party source rights remain with their respective providers.\n")
    return mem.getvalue()
