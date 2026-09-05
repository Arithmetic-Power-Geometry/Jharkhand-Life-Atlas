import streamlit as st
from jla.ui import hero
from jla.data import sources, variables, source_coverage

hero("Sources & methods", "See exactly what JLA has ingested, what authoritative sources have been identified, and what is still awaiting verified raw acquisition.")

t1,t2,t3 = st.tabs(["Coverage audit", "Source registry", "Variable registry"])
with t1:
    st.markdown("### Module 1 evidence coverage")
    st.caption("INGESTED means records are published in JLA. SOURCE_VERIFIED_RAW_NOT_BUNDLED means the authoritative source is verified but its raw records are not yet republished by JLA.")
    st.dataframe(source_coverage(), width="stretch", hide_index=True)
with t2:
    st.dataframe(sources(), width="stretch", hide_index=True)
with t3:
    st.dataframe(variables(), width="stretch", hide_index=True)

st.info("JLA keeps Census-2011 geography separate from the current Jharkhand administrative/LGD layer. Similar names do not imply identical geographic entities or time periods.")
st.warning("Source inclusion does not transfer third-party copyright or licence. JLA republishes raw source records only after source-specific reuse terms are checked.")
