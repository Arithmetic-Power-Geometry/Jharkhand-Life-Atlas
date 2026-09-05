import streamlit as st
from jla.ui import hero
from jla.data import places, sources, variables, research_bundle, dataframe_to_csv_bytes
hero("Research & download", "Build a transparent extract. Downloads include provenance and a data dictionary — not just a naked CSV.")
p=places(); s=sources(); v=variables()
try:
    levels=p.get_column('place_type').unique().sort().to_list(); level=st.selectbox('Geographic level',levels)
    out=p.filter(p['place_type']==level)
except: out=p
st.dataframe(out,width='stretch',hide_index=True)
c1,c2=st.columns(2)
with c1: st.download_button('Download CSV',data=dataframe_to_csv_bytes(out),file_name='JLA_core_geography.csv',mime='text/csv',use_container_width=True)
with c2: st.download_button('Download research bundle (.zip)',data=research_bundle(out,s,v),file_name='JLA_core_geography_research_bundle.zip',mime='application/zip',use_container_width=True)
st.caption('The research bundle includes data.csv, sources.csv, data_dictionary.csv, README and licence notes.')
