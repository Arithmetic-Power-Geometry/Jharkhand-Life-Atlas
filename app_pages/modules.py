import streamlit as st
from pathlib import Path
import yaml
from jla.ui import hero, badges, section_note
from jla.modules import discover_modules
from jla.data import module_indicators, core_research_tables, optional_core_table

hero(
    "Research the Jharkhand Life Atlas",
    "Start with a place, understand its evidence, combine thematic modules, and download reproducible research-ready data.",
    eyebrow="Modules · One geographic backbone · Forty connected evidence layers",
)

mods = [m for m in discover_modules() if not Path(m.get("_path", "")).name.startswith("_")]
by_id = {m.get("id"): m for m in mods}
roadmap_path = Path("config/module_roadmap.yaml")
try:
    raw_roadmap = (yaml.safe_load(roadmap_path.read_text(encoding="utf-8")) or {}).get("modules", [])
except Exception:
    raw_roadmap = []

roadmap = []
for entry in raw_roadmap:
    if isinstance(entry, (list, tuple)) and len(entry) >= 2:
        module_id, planned_name = entry[0], entry[1]
    elif isinstance(entry, dict):
        module_id, planned_name = entry.get("id"), entry.get("name")
    else:
        continue
    if module_id is not None:
        module_id = str(module_id)
        roadmap.append((module_id, str(planned_name) if planned_name is not None else module_id))
if not roadmap:
    roadmap = [(str(m.get("id")), str(m.get("name", m.get("id")))) for m in mods if m.get("id")]

complete_count = sum(1 for module_id, _ in roadmap if by_id.get(module_id, {}).get("status") == "complete")
active_count = sum(1 for module_id, _ in roadmap if module_id in by_id and by_id[module_id].get("status") != "complete")
pending_count = sum(1 for module_id, _ in roadmap if module_id not in by_id)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Atlas modules", len(roadmap))
c2.metric("Research-ready", complete_count)
c3.metric("In development", active_count)
c4.metric("Planned", pending_count)

section_note("Research-ready means the module has passed JLA's publication gate. In-development and planned modules remain visible so researchers can understand the full Atlas without mistaking unfinished work for published evidence.")

st.markdown("## How to use JLA for research")
a, b, c, d = st.columns(4)
with a:
    st.markdown("**1 · Find a place**")
    st.caption("Identify the district, block, panchayat, village or town and its stable JLA place identity.")
with b:
    st.markdown("**2 · Establish the baseline**")
    st.caption("Use Core Geography for Census 2011 population, amenities, administrative identity and temporal geography evidence.")
with c:
    st.markdown("**3 · Add evidence layers**")
    st.caption("Combine Health, Water, Education, livelihoods, environment, hazards and later modules through the shared place backbone.")
with d:
    st.markdown("**4 · Verify & reproduce**")
    st.caption("Inspect provenance and methods, then download research-ready evidence for analysis, reporting and citation.")

st.markdown("### Start here")
start_a, start_b, start_c = st.columns(3)
with start_a:
    if st.button("Explore a Jharkhand place", use_container_width=True, type="primary"):
        st.switch_page("app_pages/explore.py")
with start_b:
    if st.button("Download research data", use_container_width=True):
        st.switch_page("app_pages/research.py")
with start_c:
    if st.button("Check sources & methods", use_container_width=True):
        st.switch_page("app_pages/sources.py")

st.divider()
st.markdown("## Module roadmap")
st.caption("Build order is deliberate: geographic foundation → essential services → people and livelihoods → infrastructure → environment and hazards → integrated research layers.")

for number, (module_id, planned_name) in enumerate(roadmap, start=1):
    m = by_id.get(module_id)
    if m is None:
        label, detail = "PLANNED", "Implementation has not started. No evidence is published from this module."
    elif m.get("status") == "complete":
        label, detail = "RESEARCH-READY", f"v{m.get('version', '—')} · Publication gate passed."
    else:
        label, detail = "IN DEVELOPMENT", f"v{m.get('version', '—')} · Not yet certified as a complete research layer."
    with st.expander(f"{number:02d}. {planned_name}  ·  {label}", expanded=(module_id == "core_geography")):
        if m:
            st.write(m.get("description", detail))
        st.caption(detail)
        if module_id == "core_geography" and m:
            st.markdown("**What researchers can do with this module**")
            st.write("Define a study population or place; retrieve Census 2011 demographic and village-amenity baselines; identify historical Census and current LGD administrative units; and use the JLA place backbone to join later thematic modules without relying on ambiguous place names.")
            use1, use2 = st.columns(2)
            with use1:
                st.markdown("**Typical research uses**")
                st.markdown("- Village and district baseline studies\n- Population denominators for rates\n- Rural service-access sampling frames\n- Administrative and temporal geography checks\n- Place linkage for multi-module analysis")
            with use2:
                st.markdown("**Research rule**")
                st.info("Census 2011 geography and current LGD administration are separate temporal views. JLA does not silently treat them as identical.")
            tables = core_research_tables()
            st.markdown(f"**Research-ready evidence tables: {len(tables)}**")
            with st.expander("See datasets and row counts", expanded=False):
                for filename in tables:
                    try:
                        table = optional_core_table(filename)
                        rows = table.height if hasattr(table, "height") else len(table or [])
                        st.markdown(f"`{filename}` — **{rows:,} rows**")
                    except Exception as exc:
                        st.warning(f"{filename}: published but preview unavailable ({type(exc).__name__}).")
            x, y, z = st.columns(3)
            with x:
                if st.button("Explore Module 1 places", key="core_explore", use_container_width=True):
                    st.switch_page("app_pages/explore.py")
            with y:
                if st.button("Download Module 1 evidence", key="core_download", use_container_width=True):
                    st.switch_page("app_pages/research.py")
            with z:
                if st.button("Trace Module 1 sources", key="core_sources", use_container_width=True):
                    st.switch_page("app_pages/sources.py")
        elif m:
            geo = m.get("geography", {}) or {}
            badges([f"Status: {m.get('status', '—')}", f"Primary geography: {geo.get('primary', '—')}", "Valid contract" if m.get("_valid") else "Contract issue"])
            deps = ", ".join(m.get("dependencies", [])) or "None"
            st.caption(f"Dependencies: {deps}")
            if not m.get("_valid"):
                st.error("; ".join(m.get("_errors", [])))
            data = module_indicators(m.get("_path", ""))
            if data is not None:
                rows = data.height if hasattr(data, "height") else len(data)
                if rows:
                    st.markdown(f"**Published indicator rows:** {rows:,}")
                    with st.expander("Preview published module data", expanded=False):
                        st.dataframe(data, width="stretch", hide_index=True)
                else:
                    st.info("No indicator observations are published yet. Development status is not presented as completed evidence.")

st.divider()
st.markdown("## Reading the Atlas correctly")
st.markdown("**Observed** values come from identified evidence sources. **Derived** values are calculated transparently from observed evidence. **Modelled** values depend on an explicit analytical model. Missing information remains missing — it is never silently converted to zero.")
st.caption("Jharkhand Life Atlas is independent, non-partisan research infrastructure. Module status describes publication readiness, not political performance or responsibility.")
