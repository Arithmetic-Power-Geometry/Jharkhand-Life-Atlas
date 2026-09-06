import streamlit as st
from pathlib import Path
import yaml
from jla.ui import hero, badges, section_note
from jla.modules import discover_modules
from jla.data import module_indicators, core_research_tables, optional_core_table

hero(
    "Browse modules",
    "Track the complete JLA roadmap while opening every module that has reached implementation.",
    eyebrow="Modules · Build progressively, keep the whole atlas visible",
)

mods = [m for m in discover_modules() if not Path(m.get("_path", "")).name.startswith("_")]
by_id = {m.get("id"): m for m in mods}
roadmap_path = Path("config/module_roadmap.yaml")
try:
    raw_roadmap = (yaml.safe_load(roadmap_path.read_text(encoding="utf-8")) or {}).get("modules", [])
except Exception:
    raw_roadmap = []

# YAML 1.1 may parse unquoted `on` as boolean True (for example sanitation_hygiene ->
# "Sanitation & Hygiene" is safe, but roadmap values can still be non-strings). Normalize
# every roadmap entry defensively and fail over to discovered modules for malformed entries.
roadmap = []
for entry in raw_roadmap:
    if isinstance(entry, (list, tuple)) and len(entry) >= 2:
        module_id, planned_name = entry[0], entry[1]
    elif isinstance(entry, dict):
        module_id = entry.get("id")
        planned_name = entry.get("name")
    else:
        continue
    if module_id is None:
        continue
    module_id = str(module_id)
    planned_name = str(planned_name) if planned_name is not None else module_id
    roadmap.append((module_id, planned_name))

if not roadmap:
    roadmap = [(str(m.get("id")), str(m.get("name", m.get("id")))) for m in mods if m.get("id")]

complete_count = sum(1 for module_id, _ in roadmap if by_id.get(module_id, {}).get("status") == "complete")
active_count = sum(1 for module_id, _ in roadmap if module_id in by_id and by_id[module_id].get("status") != "complete")
pending_count = sum(1 for module_id, _ in roadmap if module_id not in by_id)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Roadmap modules", len(roadmap))
c2.metric("Complete", complete_count)
c3.metric("In development", active_count)
c4.metric("Pending", pending_count)

section_note("All planned modules remain visible. Complete means the module passed its publication gate; in development means implementation exists but is not yet complete; pending means its implementation has not started.")

st.markdown("### Full module stack")
for number, (module_id, planned_name) in enumerate(roadmap, start=1):
    m = by_id.get(module_id)
    if m is None:
        st.markdown(f"**{number:02d}. {planned_name}** — `PENDING`")
    else:
        status = str(m.get("status", "active")).upper()
        label = "COMPLETE" if status == "COMPLETE" else "IN DEVELOPMENT"
        st.markdown(f"**{number:02d}. {planned_name}** — `{label}` · v{m.get('version', '—')}")

st.divider()
st.markdown("## Developed module packages")

if not mods:
    st.warning("No module packages were discovered.")
else:
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
                        try:
                            table = optional_core_table(filename)
                            rows = table.height if hasattr(table, "height") else len(table or [])
                            st.markdown(f"`{filename}` — **{rows:,} rows**")
                        except Exception as exc:
                            st.warning(f"{filename}: table is published but could not be previewed ({type(exc).__name__}).")
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
