import streamlit as st
from pathlib import Path
from jla.ui import hero, badges, section_note
from jla.modules import discover_modules
from jla.data import module_indicators, core_research_tables, optional_core_table

hero(
    "Browse modules",
    "Each JLA module is independent, evidence-aware and discoverable from its folder. New modules can be added later without redesigning the platform.",
    eyebrow="Modules · Expand without rebuilding",
)

mods = [m for m in discover_modules() if not Path(m.get("_path", "")).name.startswith("_")]

if not mods:
    st.warning("No modules were discovered.")
else:
    c1, c2, c3 = st.columns(3)
    c1.metric("Discovered modules", len(mods))
    c2.metric("Operational", sum(1 for m in mods if m.get("_valid")))
    c3.metric("Needs attention", sum(1 for m in mods if not m.get("_valid")))

    section_note("Module status describes the current published package, not the completeness of every possible source dataset. JLA keeps those two ideas separate.")

    for m in mods:
        title = m.get("name", m.get("id", "Unnamed module"))
        version = m.get("version", "—")
        status = m.get("status", "—")
        with st.container(border=True):
            top_a, top_b = st.columns([4, 1])
            with top_a:
                st.markdown(f"### {title}")
                st.write(m.get("description", "No description supplied."))
            with top_b:
                st.metric("Version", version)

            geo = m.get("geography", {}) or {}
            badges([
                f"Status: {status}",
                f"Primary geography: {geo.get('primary', '—')}",
                "Valid contract" if m.get("_valid") else "Contract issue",
            ])

            if not m.get("_valid"):
                st.error("; ".join(m.get("_errors", [])))

            deps = ", ".join(m.get("dependencies", [])) or "None"
            st.caption(f"Dependencies: {deps}")

            if m.get("id") == "core_geography":
                tables = core_research_tables()
                st.markdown(f"**Published curated evidence tables:** {len(tables)}")
                with st.expander("View Core Geography datasets", expanded=False):
                    for filename in tables:
                        table = optional_core_table(filename)
                        try:
                            rows = table.height if table is not None else 0
                        except Exception:
                            rows = len(table) if table is not None else 0
                        st.markdown(f"`{filename}` — **{rows:,} rows**")
                st.caption("Includes Census 2011 geography/demography, DCHB village amenities, MDDS 2001↔2011 evidence, current LGD layers and the conservative Census↔LGD temporal view.")
                continue

            data = module_indicators(m.get("_path", ""))
            if data is not None:
                try:
                    empty = data.height == 0
                    rows = data.height
                except Exception:
                    empty = len(data) == 0
                    rows = len(data)
                if empty:
                    st.info("Module contract is active; no indicator observations have been published yet.", icon="ℹ️")
                else:
                    st.markdown(f"**Published indicator rows:** {rows}")
                    with st.expander("View module data", expanded=False):
                        st.dataframe(data, width="stretch", hide_index=True)
