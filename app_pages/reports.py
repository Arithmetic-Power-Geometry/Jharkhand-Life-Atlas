from pathlib import Path
import json

import streamlit as st
from jla.ui import hero, section_note
from jla.data import places, sources, optional_core_table
from jla.reports import pdf_report, html_report

hero(
    "Generate report",
    "Create a portable evidence profile with source references, Module 1 evidence-layer status, validated thematic-evidence coverage and interpretation safeguards.",
)
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


def _validated_historical_evidence():
    """Return only thematic datasets whose committed provenance passes the public historical gate.

    This intentionally reports evidence availability only. It never joins thematic values to a
    selected current place or infers temporal/geographic equivalence from names.
    """
    candidates = [
        (2, "Health", "health_access", "census_health_access_2011"),
        (3, "Water", "water_access", "census_water_access_2011"),
        (4, "Sanitation & Hygiene", "sanitation_hygiene", "census_sanitation_hygiene_2011"),
        (5, "Education", "education_access", "census_education_access_2011"),
    ]
    verified = []
    for number, label, slug, filename in candidates:
        csv_path = Path(f"data/curated/{slug}/{filename}.csv")
        provenance_path = csv_path.with_suffix(".provenance.json")
        if not (csv_path.exists() and provenance_path.exists()):
            continue
        try:
            meta = json.loads(provenance_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if meta.get("status") != "validated_source_native_historical_extract":
            continue
        if int(meta.get("reference_year", 0)) != 2011:
            continue
        if meta.get("output") != str(csv_path):
            continue
        if not meta.get("output_sha256") or not meta.get("source_sha256"):
            continue
        verified.append(
            {
                "module": f"Module {number} — {label}",
                "status": "validated historical evidence available",
                "reference_year": 2011,
                "rows": int(meta.get("row_count", 0)),
                "source_native_fields": int(meta.get("health_field_count", meta.get("thematic_field_count", 0))),
                "output_sha256": meta.get("output_sha256"),
                "source_sha256": meta.get("source_sha256"),
            }
        )
    return verified


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

verified_thematic = _validated_historical_evidence()
thematic_summary = {
    "thematic_evidence_status": "validated historical datasets only",
    "validated_thematic_modules": len(verified_thematic),
    "modules": "; ".join(x["module"] for x in verified_thematic) if verified_thematic else "none",
    "interpretation_guard": "Availability here does not imply current service status and does not authorize Census-2011/current-LGD equivalence.",
}

try:
    report_rows = row.to_dicts() + [summary, thematic_summary] + verified_thematic
except Exception:
    base_rows = row if isinstance(row, list) else []
    report_rows = base_rows + [summary, thematic_summary] + verified_thematic

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

section_note(
    "Reports preserve the distinction between missing evidence and zero, historical Census geography and current LGD administration, and validated historical thematic evidence versus current service availability."
)

if verified_thematic:
    st.markdown("### Validated thematic evidence included in report metadata")
    for item in verified_thematic:
        st.caption(
            f"{item['module']} · {item['rows']:,} rows · {item['source_native_fields']} source-native fields · reference year 2011"
        )
    st.info(
        "These thematic datasets are reported as evidence coverage only. This report does not silently join their 2011 observations to current administrative units or reinterpret them as current conditions."
    )

if st.button("Prepare report", type="primary"):
    pdf = pdf_report(f"Evidence Profile — {name}", report_rows, refs, release="1.2.0")
    html = html_report(f"Evidence Profile — {name}", report_rows, refs, release="1.2.0")
    c1, c2 = st.columns(2)
    c1.download_button("Download PDF", pdf, file_name=f'JLA_{name.replace(" ","_")}_Evidence_Profile.pdf', mime="application/pdf", use_container_width=True)
    c2.download_button("Download HTML", html, file_name=f'JLA_{name.replace(" ","_")}_Evidence_Profile.html', mime="text/html", use_container_width=True)
