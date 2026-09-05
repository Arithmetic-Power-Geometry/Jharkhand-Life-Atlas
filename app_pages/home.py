import streamlit as st
from jla.ui import hero, card, badges, section_note
from jla.modules import discover_modules
from jla.data import places, sources, variables

hero(
    "Understand a place. Find a need. Trace the evidence.",
    "Jharkhand Life Atlas connects geography, public-interest data and source evidence in one modular research platform. Start with Core Geography today; future modules plug into the same structure without rebuilding the app.",
)

p = places()
s = sources()
v = variables()
mods = [m for m in discover_modules() if not m.get("id", "").startswith("example")]

try:
    n_places, n_sources, n_vars = p.height, s.height, v.height
except Exception:
    n_places, n_sources, n_vars = len(p), len(s), len(v)

badges(["Open data", "Evidence-preserving", "Village-ready", "Modular", "Research-friendly"])

st.markdown("### At a glance")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Verified places", n_places, help="Records bundled and validated in the current release")
c2.metric("Active modules", len(mods))
c3.metric("Data variables", n_vars)
c4.metric("Registered sources", n_sources)

section_note(
    "Current release status: the software and module framework are operational. Core Geography currently contains a verified 24-district Jharkhand baseline; village, block and panchayat records are added only when authoritative source files are verified. Missing data is never invented."
)

st.markdown("### Quick access")
a, b, c, d = st.columns(4)
with a:
    card("Explore places", "Browse the geographic backbone and inspect the evidence attached to each place.", "📍")
    st.page_link("app_pages/explore.py", label="Open explorer", icon="🔎", use_container_width=True)
with b:
    card("Browse modules", "See what each module contains, its status, geography and published observations.", "🧩")
    st.page_link("app_pages/modules.py", label="Open modules", icon="🗂️", use_container_width=True)
with c:
    card("Download data", "Create a transparent research extract with sources, dictionary and licence notes.", "⬇️")
    st.page_link("app_pages/research.py", label="Open downloads", icon="📦", use_container_width=True)
with d:
    card("Generate report", "Create an evidence profile in PDF or HTML with references attached.", "📄")
    st.page_link("app_pages/reports.py", label="Open reports", icon="🧾", use_container_width=True)

st.markdown("### How JLA works")
x, y, z = st.columns(3)
with x:
    card("1 · Place first", "Every record anchors to a stable place identity so future health, water, education, agriculture and risk modules can connect cleanly.", "🗺️")
with y:
    card("2 · Evidence always visible", "Values retain source, year, method, observation type and quality so researchers can audit what they use.", "🔗")
with z:
    card("3 · Modules grow independently", "New societal modules can be added under modules/ and discovered by the app without rewriting the core platform.", "➕")

st.markdown("### Evidence rule")
st.success("Every published value should be traceable: **value → variable → source → year → method → quality**. Missing data is not zero, and unsupported values are not published.", icon="✅")
