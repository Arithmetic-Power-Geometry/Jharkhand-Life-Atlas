import streamlit as st
from jla.ui import hero
from jla.data import places, sources
from jla.reports import pdf_report, html_report
hero("Generate report", "Create a portable evidence profile with source references and interpretation safeguards.")
p=places(); s=sources()
try:
    names=p.get_column('name').sort().to_list(); name=st.selectbox('Place',names); row=p.filter(p['name']==name); sid=row.get_column('source_id')[0]; refs=s.filter(s['source_id']==sid)
except Exception:
    name='Jharkhand'; row=p; refs=s
if st.button('Prepare report',type='primary'):
    pdf=pdf_report(f"Evidence Profile — {name}",row,refs); html=html_report(f"Evidence Profile — {name}",row,refs)
    c1,c2=st.columns(2)
    c1.download_button('Download PDF',pdf,file_name=f'JLA_{name.replace(" ","_")}_Evidence_Profile.pdf',mime='application/pdf',use_container_width=True)
    c2.download_button('Download HTML',html,file_name=f'JLA_{name.replace(" ","_")}_Evidence_Profile.html',mime='text/html',use_container_width=True)
