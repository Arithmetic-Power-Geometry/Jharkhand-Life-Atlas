from pathlib import Path
import json

import streamlit as st
from jla.ui import hero, badges, section_note
from jla.data import places, sources, variables, research_bundle, dataframe_to_csv_bytes, core_research_tables

hero(
    "Download data",
    "Choose the geographic level you need and download verified research evidence. Module 1 remains the complete geographic backbone; validated thematic evidence is added here only after its own provenance and validation gates pass.",
    eyebrow="Research tools · Transparent extracts",
)

p = places()
s = sources()
v = variables()

try:
    levels = p.get_column("place_type").unique().sort().to_list()
    level = st.selectbox("Geographic level", levels)
    out = p.filter(p["place_type"] == level)
    row_count = out.height
except Exception:
    out = p
    row_count = len(out)
    level = "all"

included = core_research_tables()
badges([f"Level: {level}", f"Rows: {row_count}", f"Core tables: {len(included)}", "Provenance included"])
section_note("For reproducible research, prefer the Module 1 research bundle. The separate Health download below is a validated historical Census 2011 source-native projection and must not be interpreted as current facility availability.")

preview, provenance = st.tabs(["Data preview", "What is included"])
with preview:
    st.dataframe(out, width="stretch", hide_index=True)
with provenance:
    st.markdown("**Research bundle contents**")
    st.markdown("- `data.csv` — selected JLA place records\n- `sources.csv` — provenance/source registry\n- `data_dictionary.csv` — variable definitions\n- `core_geography/` — verified Module 1 curated tables\n- `README.txt` — extract context and temporal safeguards\n- `LICENSE.txt` — JLA licensing notes")
    with st.expander("View included Module 1 tables", expanded=False):
        for filename in included:
            st.code(f"core_geography/{filename}")
    st.caption("Third-party source material retains its own source terms; JLA does not silently relicense external datasets. Missing values are not interpreted as zero, and Census 2011 remains separate from current LGD unless an authoritative crosswalk supports linkage.")

st.markdown("### Module 1 download")
c1, c2 = st.columns(2)
with c1:
    st.download_button(
        "Download CSV",
        data=dataframe_to_csv_bytes(out),
        file_name="JLA_core_geography.csv",
        mime="text/csv",
        use_container_width=True,
        icon="📄",
    )
    st.caption("Best for quick inspection and spreadsheet use.")
with c2:
    st.download_button(
        "Download research bundle (.zip)",
        data=research_bundle(out, s, v),
        file_name="JLA_core_geography_research_bundle.zip",
        mime="application/zip",
        use_container_width=True,
        icon="📦",
    )
    st.caption("Recommended for research, reuse and citation.")

health_csv = Path("data/curated/health_access/census_health_access_2011.csv")
health_provenance = Path("data/curated/health_access/census_health_access_2011.provenance.json")
if health_csv.exists() and health_provenance.exists():
    try:
        health_meta = json.loads(health_provenance.read_text(encoding="utf-8"))
    except Exception:
        health_meta = {}
    if health_meta.get("status") == "validated_source_native_historical_extract":
        st.divider()
        st.markdown("### Module 2 · validated historical Health evidence")
        h1, h2, h3 = st.columns(3)
        h1.metric("Historical rows", f"{int(health_meta.get('row_count', 0)):,}")
        h2.metric("Health source fields", int(health_meta.get("health_field_count", 0)))
        h3.metric("Reference year", health_meta.get("reference_year", "—"))
        st.info("This is a direct source-native projection of the already-governed Census 2011 village amenities evidence. It contains historical CHC, PHC, health sub-centre, maternity/child welfare, TB clinic, hospital, dispensary, mobile-clinic, family-welfare and non-government medical-facility fields. It is not a current-facility dataset and is not remapped to current administrative units.")
        st.caption(f"Output SHA-256: {health_meta.get('output_sha256', '—')} · Source SHA-256: {health_meta.get('source_sha256', '—')}")
        st.download_button(
            "Download validated Census 2011 Health evidence",
            data=health_csv.read_bytes(),
            file_name="JLA_health_access_census_2011.csv",
            mime="text/csv",
            use_container_width=True,
            icon="🩺",
        )
        st.caption("Missing source values remain missing. No missing value was converted to zero; no imputation, aggregation, current-geography equivalence or derived availability claim was introduced.")
