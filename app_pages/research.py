import streamlit as st
from jla.ui import hero
from jla.data import places, sources, variables, reconciliation, census_pca_catalog, research_bundle, dataframe_to_csv_bytes

hero("Research & download", "Build a self-describing extract. Provenance, dictionary, conflict audit and source-discovery status travel with the data.", ["CSV", "Research ZIP", "Provenance included"])
p=places()
level=st.selectbox('Geographic level',['all','state','division','district','subdivision','block'],index=0)
out=p if level=='all' else p.filter(p['place_type']==level)
if level in {'district','subdivision','block'}:
    districts=['All']+sorted(out.get_column('district').drop_nulls().unique().to_list())
    d=st.selectbox('District filter',districts)
    if d!='All': out=out.filter(out['district']==d)
st.dataframe(out,width='stretch',hide_index=True)
c1,c2=st.columns(2)
with c1: st.download_button('Download selected places CSV',data=dataframe_to_csv_bytes(out),file_name='JLA_core_geography_selection.csv',mime='text/csv',use_container_width=True)
with c2: st.download_button('Download complete research bundle (.zip)',data=research_bundle(out,sources(),variables()),file_name='JLA_v1.1.0_core_geography_research_bundle.zip',mime='application/zip',use_container_width=True)

st.subheader('What the bundle contains')
st.markdown('`data.csv` · `sources.csv` · `data_dictionary.csv` · `core/current_blocks.csv` · `core/state_facts_2011.csv` · `core/census_pca_catalog.csv` · `core/reconciliation.csv` · README/licence notes')

st.subheader('Audit preview')
a,b=st.columns(2)
with a:
    st.markdown('**Official-source reconciliation**'); st.dataframe(reconciliation(),width='stretch',hide_index=True)
with b:
    cat=census_pca_catalog(); st.metric('Official district PCA catalogs indexed',cat.height); st.metric('Raw PCA district files bundled',0)
    st.caption('Catalog coverage is explicit; raw village-level ingestion is a separate validation stage.')
