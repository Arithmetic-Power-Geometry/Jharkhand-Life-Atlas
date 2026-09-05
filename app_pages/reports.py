import streamlit as st
from jla.ui import hero
from jla.data import places, current_blocks, sources
from jla.reports import pdf_report, html_report

hero("Generate evidence report", "Create a portable place profile with its actual source references and interpretation safeguards.", ["PDF", "HTML", "References embedded"])
p=places(); b=current_blocks(); s=sources()
level=st.radio('Profile level',['District','Block'],horizontal=True)
if level=='District':
    names=sorted(p.filter(p['place_type']=='district').get_column('name').to_list())
    name=st.selectbox('District',names)
    rows=b.filter(b['district']==name)
    refs=s.filter(s['source_id'].is_in(rows.get_column('source_id').unique().to_list()))
    title=f'Evidence Profile — {name} District'
else:
    districts=sorted(b.get_column('district').unique().to_list()); d=st.selectbox('District',districts)
    names=sorted(b.filter(b['district']==d).get_column('block').to_list()); name=st.selectbox('Block',names)
    rows=b.filter((b['district']==d)&(b['block']==name))
    refs=s.filter(s['source_id'].is_in(rows.get_column('source_id').unique().to_list()))
    title=f'Evidence Profile — {name} Block, {d}'
st.dataframe(rows,width='stretch',hide_index=True)
if st.button('Prepare report',type='primary'):
    pdf=pdf_report(title,rows,refs,release='1.1.0'); html=html_report(title,rows,refs,release='1.1.0')
    c1,c2=st.columns(2)
    safe=name.replace(' ','_').replace('/','-')
    c1.download_button('Download PDF',pdf,file_name=f'JLA_{safe}_Evidence_Profile.pdf',mime='application/pdf',use_container_width=True)
    c2.download_button('Download HTML',html,file_name=f'JLA_{safe}_Evidence_Profile.html',mime='text/html',use_container_width=True)
