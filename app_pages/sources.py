import streamlit as st
from jla.ui import hero
from jla.data import sources, variables
hero("Sources & methods", "The provenance registry is a first-class dataset. Every module should register its evidence before publishing indicators.")
st.subheader('Source registry'); st.dataframe(sources(),width='stretch',hide_index=True)
st.subheader('Variable registry'); st.dataframe(variables(),width='stretch',hide_index=True)
st.warning('Source inclusion does not transfer third-party copyright or licence. Verify source-specific reuse terms before redistributing raw files.')
