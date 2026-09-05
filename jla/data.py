from __future__ import annotations
from pathlib import Path
import csv, io, zipfile
try:
    import polars as pl
except Exception:
    pl = None
from .paths import DATA_DIR, REGISTRY_DIR

CORE = DATA_DIR / "curated" / "core_geography"

def read_csv(path: Path):
    if pl is None:
        with path.open(encoding="utf-8", newline="") as f:
            return list(csv.DictReader(f))
    return pl.read_csv(path, infer_schema_length=10000, null_values=["", "NA", "N/A", "null"])

def places(): return read_csv(CORE / "places.csv")
def current_blocks(): return read_csv(CORE / "current_blocks.csv")
def state_facts(): return read_csv(CORE / "state_facts_2011.csv")
def census_pca_catalog(): return read_csv(CORE / "census_pca_catalog.csv")
def reconciliation(): return read_csv(CORE / "reconciliation.csv")
def sources(): return read_csv(REGISTRY_DIR / "sources.csv")
def variables(): return read_csv(REGISTRY_DIR / "variables.csv")

def module_indicators(module_path: str):
    p = Path(module_path) / "data" / "indicators.csv"
    return read_csv(p) if p.exists() else None

def dataframe_to_csv_bytes(df) -> bytes:
    if pl is not None and isinstance(df, pl.DataFrame):
        return df.write_csv().encode("utf-8")
    if not df: return b""
    out = io.StringIO()
    w = csv.DictWriter(out, fieldnames=list(df[0].keys()))
    w.writeheader(); w.writerows(df)
    return out.getvalue().encode()

def research_bundle(data_df=None, source_df=None, variable_df=None, name="JLA_extract") -> bytes:
    """Create a self-describing research ZIP. Core audit tables are always included."""
    data_df = places() if data_df is None else data_df
    source_df = sources() if source_df is None else source_df
    variable_df = variables() if variable_df is None else variable_df
    mem = io.BytesIO()
    with zipfile.ZipFile(mem, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("data.csv", dataframe_to_csv_bytes(data_df))
        z.writestr("sources.csv", dataframe_to_csv_bytes(source_df))
        z.writestr("data_dictionary.csv", dataframe_to_csv_bytes(variable_df))
        z.writestr("core/current_blocks.csv", dataframe_to_csv_bytes(current_blocks()))
        z.writestr("core/state_facts_2011.csv", dataframe_to_csv_bytes(state_facts()))
        z.writestr("core/census_pca_catalog.csv", dataframe_to_csv_bytes(census_pca_catalog()))
        z.writestr("core/reconciliation.csv", dataframe_to_csv_bytes(reconciliation()))
        z.writestr("README.txt", (
            "Jharkhand Life Atlas v1.1.0 research extract.\n"
            "Cite JLA and each underlying source listed in sources.csv.\n"
            "Missing values are not zero. Official-source disagreements are preserved in core/reconciliation.csv.\n"
            "PCA catalog discovery is not equivalent to raw village-record ingestion.\n"
        ))
        z.writestr("LICENSE.txt", "JLA original material: CC BY 4.0. Third-party source rights remain with their respective providers.\n")
    return mem.getvalue()
