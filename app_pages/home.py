import streamlit as st
from jla.ui import hero, status_note
from jla.modules import discover_modules
from jla.data import places, sources, reconciliation, state_facts

hero(
    "Understand a place. Find a need. Trace the evidence.",
    "A modular public-interest evidence infrastructure for Jharkhand. Module 1 establishes the administrative spine and Census baseline without hiding source disagreements.",
    ["5 divisions", "24 districts", "45 subdivisions", "264 blocks", "Evidence-first"]
)
p=places(); s=sources(); mods=[m for m in discover_modules() if not m['id'].startswith('example')]
counts={t:p.filter(p['place_type']==t).height for t in ['division','district','subdivision','block']}
c1,c2,c3,c4,c5=st.columns(5)
c1.metric("Divisions", counts['division'])
c2.metric("Districts", counts['district'])
c3.metric("Subdivisions", counts['subdivision'])
c4.metric("Blocks", counts['block'])
c5.metric("Registered sources", s.height)

status_note("<b>Module 1 v1.1.0:</b> current administrative hierarchy is validated through block level. The official 24-district Census PCA catalog is indexed. Full village/PCA/amenities raw records are <b>not</b> claimed as ingested until the official raw files are retrieved and validated.")

st.subheader("What is already usable")
a,b,c=st.columns(3)
with a: st.markdown('<div class="jla-card"><b>🔎 Place Explorer</b><br><br>Navigate division → district → subdivision → block, inspect source-reported panchayat/village counts, and open provenance.</div>',unsafe_allow_html=True)
with b: st.markdown('<div class="jla-card"><b>🧪 Research Extracts</b><br><br>Download the hierarchy together with sources, data dictionary, source-conflict audit and Census source catalog.</div>',unsafe_allow_html=True)
with c: st.markdown('<div class="jla-card"><b>📄 Evidence Reports</b><br><br>Create portable PDF/HTML profiles that carry source references and interpretation safeguards.</div>',unsafe_allow_html=True)

st.subheader("Evidence status")
rec=reconciliation()
conflicts=rec.filter(rec['status']!='reconciled')
col1,col2=st.columns([1.15,1])
with col1:
    st.markdown("**Official-source reconciliation**")
    st.dataframe(rec, width='stretch', hide_index=True)
with col2:
    st.markdown("**Why this matters**")
    st.write("Official Jharkhand pages currently publish different totals for some administrative measures. JLA preserves those snapshots instead of silently choosing a convenient number.")
    st.metric("Unresolved / temporal differences", conflicts.height)
    st.caption("A disagreement is an evidence property, not an error to erase.")

st.subheader("2011 state baseline")
f=state_facts()
keep=['population_total','literacy_rate','sex_ratio','st_share','sc_share','population_density']
show=f.filter(f['indicator_id'].is_in(keep)).select(['indicator_id','value_numeric','unit','period','source_id'])
st.dataframe(show,width='stretch',hide_index=True)

st.caption("Design rule: value → variable → source → year → observation type → quality. Missing data is never silently treated as zero.")
