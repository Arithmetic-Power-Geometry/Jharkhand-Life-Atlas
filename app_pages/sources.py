import streamlit as st
from jla.ui import hero, status_note
from jla.data import sources, variables, census_pca_catalog, reconciliation

hero("Sources, methods & audit", "See exactly where JLA facts came from, what has been ingested, and where official sources disagree.", ["Traceable", "Source-specific", "Conflict-aware"])
t1,t2,t3,t4=st.tabs(['Source registry','Census PCA catalog','Reconciliation','Data dictionary'])
with t1:
    st.dataframe(sources(),width='stretch',hide_index=True)
    st.caption('Source registration does not transfer third-party copyright or licence. Source-specific terms remain controlling.')
with t2:
    cat=census_pca_catalog(); st.metric('District catalog records',cat.height)
    st.dataframe(cat,width='stretch',hide_index=True,column_config={'catalog_url':st.column_config.LinkColumn('Official Census catalog')})
    status_note('<b>Ingestion boundary:</b> all 24 district PCA catalog entries are indexed, but the raw XLSX village/town records are not represented as curated values until retrieved and validated.')
with t3:
    rec=reconciliation(); st.dataframe(rec,width='stretch',hide_index=True)
    st.write('JLA preserves conflicting official snapshots with notes and status flags. This prevents temporal or definitional differences from being disguised as certainty.')
with t4:
    st.dataframe(variables(),width='stretch',hide_index=True)

st.subheader('Method rules')
st.markdown('''
- **No source = no published factual value.**
- **Missing ≠ zero.**
- Observed source snapshots, derived identifiers and audits are labelled separately.
- JLA-derived `place_id` values never masquerade as official Census/LGD codes.
- Catalog discovery is not the same thing as raw-record ingestion.
- JLA is non-partisan and does not attribute responsibility to parties, elected representatives or governments.
''')
