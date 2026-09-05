import streamlit as st
from jla.ui import hero, section_note
from jla.data import places, sources, optional_core_table
from jla.reports import pdf_report, html_report

hero("Generate report", "Create a portable evidence profile with source references, Module 1 evidence-layer status and interpretation safeguards.")
p = places()
s = sources()

try:
    names = p.get_column("name").sort().to_list()
    name = st.selectbox("Place", names)
    row = p.filter(p["name"] == name)
    record = row.to_dicts()[0]
except Exception:
    name = "Jharkhand"
    row = p
    record = {}

amenities = optional_core_table("village_amenities_2011.csv")
mdds = optional_core_table("census_mdds_crosswalk_2001_2011.csv")
temporal = optional_core_table("census_lgd_temporal_crosswalk.csv")
code = str(record.get("village_code") or "").strip()


def _match(table, field, value):
    if table is None or not value:
        return None
    try:
        if field not in table.columns:
            return None
        return table.filter(table[field].cast(str).str.strip_chars() == value)
    except Exception:
        return None

amen_match = _match(amenities, "census_village_code_2011", code)
mdds_match = _match(mdds, "census_village_code_2011", code)
temporal_match = _match(temporal, "census_village_code_2011", code)

summary = {
    "module": "Core Geography & Census Baseline",
    "module_status": "complete authoritative available layers",
    "dchb_amenities_link": "verified row available" if getattr(amen_match, "height", 0) else "not available/not applicable for this selected place",
    "mdds_2001_2011_link": "verified row available" if getattr(mdds_match, "height", 0) else "not available/not applicable for this selected place",
    "census_lgd_temporal_record": "explicit temporal record available" if getattr(temporal_match, "height", 0) else "not available/not applicable for this selected place",
    "temporal_safeguard": "Census 2011 and current LGD are kept separate unless an authoritative code linkage is exposed.",
}

try:
    report_rows = row.to_dicts() + [summary]
except Exception:
    report_rows = row + [summary] if isinstance(row, list) else [summary]

module_source_ids = {
    "CENSUS_LOCATION_DIR_2011",
    "CENSUS_BASIC_2011",
    "CENSUS_MDDS_JH_2011",
    "CENSUS_DCHB_JH_2011",
    "OGD_PCA_JH_2011",
    "LGD_CURRENT",
}
try:
    refs = s.filter(s["source_id"].is_in(list(module_source_ids)))
except Exception:
    refs = s

section_note("Reports preserve the distinction between missing evidence and zero, and between historical Census geography and current LGD administration.")

if st.button("Prepare report", type="primary"):
    pdf = pdf_report(f"Evidence Profile — {name}", report_rows, refs, release="1.2.0")
    html = html_report(f"Evidence Profile — {name}", report_rows, refs, release="1.2.0")
    c1, c2 = st.columns(2)
    c1.download_button("Download PDF", pdf, file_name=f'JLA_{name.replace(" ","_")}_Evidence_Profile.pdf', mime="application/pdf", use_container_width=True)
    c2.download_button("Download HTML", html, file_name=f'JLA_{name.replace(" ","_")}_Evidence_Profile.html', mime="text/html", use_container_width=True)
