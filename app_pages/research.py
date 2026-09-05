import streamlit as st
from jla.ui import hero, badges, section_note
from jla.data import places, sources, variables, research_bundle, dataframe_to_csv_bytes

hero(
    "Download data",
    "Choose the geographic level you need and download either a simple CSV or a research bundle containing the evidence needed to understand and cite it.",
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

badges([f"Level: {level}", f"Rows: {row_count}", "Source registry included", "Data dictionary included"])
section_note("For reproducible research, prefer the research bundle. It packages the selected data together with sources, variable definitions, README and licence notes.")

preview, provenance = st.tabs(["Data preview", "What is included"])
with preview:
    st.dataframe(out, width="stretch", hide_index=True)
with provenance:
    st.markdown("**Research bundle contents**")
    st.markdown("- `data.csv` — selected JLA records\n- `sources.csv` — provenance/source registry\n- `data_dictionary.csv` — variable definitions\n- `README.txt` — extract context\n- `LICENSE.txt` — JLA licensing notes")
    st.caption("Third-party source material retains its own source terms; JLA does not silently relicense external datasets.")

st.markdown("### Download")
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
