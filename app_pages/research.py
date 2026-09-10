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
section_note("For reproducible research, prefer the Module 1 research bundle. Separate thematic downloads below are exposed only when their provenance explicitly records a validated source-native historical extract. Historical evidence must not be interpreted as current service availability.")

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


def validated_historical_download(
    *,
    module_number: int,
    module_name: str,
    slug: str,
    filename: str,
    field_label: str,
    field_count_key: str,
    description: str,
    icon: str,
) -> None:
    csv_path = Path(f"data/curated/{slug}/{filename}.csv")
    provenance_path = csv_path.with_suffix(".provenance.json")
    if not (csv_path.exists() and provenance_path.exists()):
        return
    try:
        meta = json.loads(provenance_path.read_text(encoding="utf-8"))
    except Exception:
        return
    if meta.get("status") != "validated_source_native_historical_extract":
        return
    if int(meta.get("reference_year", 0)) != 2011:
        return
    if meta.get("output") != str(csv_path):
        return
    if not meta.get("output_sha256") or not meta.get("source_sha256"):
        return

    st.divider()
    st.markdown(f"### Module {module_number} · validated historical {module_name} evidence")
    m1, m2, m3 = st.columns(3)
    m1.metric("Historical rows", f"{int(meta.get('row_count', 0)):,}")
    m2.metric(field_label, int(meta.get(field_count_key, meta.get("thematic_field_count", 0))))
    m3.metric("Reference year", meta.get("reference_year", "—"))
    st.info(description)
    st.caption(f"Output SHA-256: {meta.get('output_sha256')} · Source SHA-256: {meta.get('source_sha256')}")
    st.download_button(
        f"Download validated Census 2011 {module_name} evidence",
        data=csv_path.read_bytes(),
        file_name=f"JLA_{slug}_census_2011.csv",
        mime="text/csv",
        use_container_width=True,
        icon=icon,
        key=f"download_{slug}_2011",
    )
    st.caption("Missing source values remain missing. No missing value was converted to zero; no imputation, aggregation, current-geography equivalence or current-status claim was introduced.")


validated_historical_download(
    module_number=2,
    module_name="Health",
    slug="health_access",
    filename="census_health_access_2011",
    field_label="Health source fields",
    field_count_key="health_field_count",
    description="This is a direct source-native projection of the already-governed Census 2011 village amenities evidence. It contains historical health-facility amenity fields and is not a current-facility dataset or a current administrative-geography view.",
    icon="🩺",
)

validated_historical_download(
    module_number=3,
    module_name="Water",
    slug="water_access",
    filename="census_water_access_2011",
    field_label="Water source fields",
    field_count_key="thematic_field_count",
    description="This is a reviewed direct projection of Census 2011 village water-amenity fields, including treated/untreated tap water, wells, hand pumps, boreholes, springs, rivers/canals and tanks/ponds/lakes with source-native functioning fields. It is historical evidence, not current Jal Jeevan Mission coverage.",
    icon="💧",
)

validated_historical_download(
    module_number=4,
    module_name="Sanitation & Hygiene",
    slug="sanitation_hygiene",
    filename="census_sanitation_hygiene_2011",
    field_label="Sanitation source fields",
    field_count_key="thematic_field_count",
    description="This is a reviewed direct projection of Census 2011 village sanitation/hygiene amenity fields covering drainage, sanitation-campaign status, community-toilet complexes and source-native waste/drainage fields. It is not current SBM-G or ODF Plus status.",
    icon="🚻",
)

validated_historical_download(
    module_number=5,
    module_name="Education",
    slug="education_access",
    filename="census_education_access_2011",
    field_label="Education source fields",
    field_count_key="thematic_field_count",
    description="This is a reviewed direct projection of Census 2011 village education-amenity fields spanning source-native government/private school, college, vocational/ITI and disability-school status/count fields. It is historical evidence, not current UDISE+ school status.",
    icon="🎓",
)
