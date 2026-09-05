import streamlit as st
from jla.ui import hero
from jla.modules import discover_modules
from jla.data import places, sources, variables
hero("Understand a place. Find a need. Trace the evidence.", "A modular public-interest evidence infrastructure for Jharkhand — designed to grow from geography into health, water, education, agriculture, climate, human–wildlife conflict and future societal modules.")
p=places(); s=sources(); v=variables(); mods=[m for m in discover_modules() if not m['id'].startswith('example')]
try: n_places=p.height; n_sources=s.height; n_vars=v.height
except: n_places=len(p); n_sources=len(s); n_vars=len(v)
c1,c2,c3,c4=st.columns(4)
c1.metric("Bundled places",n_places,help="Verified baseline records in this release")
c2.metric("Discovered modules",len(mods))
c3.metric("Registered variables",n_vars)
c4.metric("Registered sources",n_sources)
st.info("**v1.0.0 foundation release:** Core Geography is fully operational. The bundled data are a verified 24-district Census baseline. Village/block/panchayat records are intentionally not fabricated and are added only from reviewed authoritative source files.", icon="ℹ️")
st.subheader("What you can do now")
a,b,c=st.columns(3)
with a: st.markdown('<div class="jla-card"><b>🔎 Explore evidence</b><br><br>Browse the Jharkhand geography baseline and see source, quality and temporal metadata.</div>',unsafe_allow_html=True)
with b: st.markdown('<div class="jla-card"><b>⬇️ Build research extracts</b><br><br>Download data together with its dictionary, sources and licence notes.</div>',unsafe_allow_html=True)
with c: st.markdown('<div class="jla-card"><b>📄 Generate evidence reports</b><br><br>Create PDF/HTML reports with references automatically attached.</div>',unsafe_allow_html=True)
st.subheader("Design rule")
st.markdown("**Every published value should be traceable:** value → variable → source → year → method → quality. Missing data is never silently treated as zero.")
