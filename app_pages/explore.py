import streamlit as st
from jla.ui import hero
from jla.data import places, sources
hero("Explore places", "Start with the authoritative geography backbone. As village-level crosswalks are added, this same page expands automatically.")
df=places()
try:
    types=df.get_column('place_type').unique().sort().to_list(); typ=st.selectbox('Geographic level',types)
    sub=df.filter(df['place_type']==typ)
    names=sub.get_column('name').sort().to_list(); name=st.selectbox('Place',names)
    row=sub.filter(sub['name']==name)
    st.dataframe(row, width='stretch', hide_index=True)
    src_id=row.get_column('source_id')[0]; src=sources().filter(sources()['source_id']==src_id)
    with st.expander('Evidence and provenance', expanded=True): st.dataframe(src,width='stretch',hide_index=True)
except Exception:
    st.dataframe(df,width='stretch',hide_index=True)
