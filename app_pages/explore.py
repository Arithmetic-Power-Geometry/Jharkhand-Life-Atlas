import streamlit as st
from jla.ui import hero, status_note
from jla.data import places, current_blocks, sources

hero("Explore Jharkhand", "Navigate the verified administrative hierarchy through block level and inspect the evidence behind each record.", ["Current hierarchy", "Source snapshots", "No invented coordinates"])
p=places(); b=current_blocks(); src=sources()

c1,c2,c3,c4=st.columns(4)
divisions=sorted(p.filter(p['place_type']=='division').get_column('name').to_list())
div= c1.selectbox('Division', divisions)
districts=sorted(p.filter((p['place_type']=='district') & (p['division']==div)).get_column('name').to_list())
district=c2.selectbox('District', districts)
subdivisions=sorted(p.filter((p['place_type']=='subdivision') & (p['district']==district)).get_column('name').to_list())
subdiv=c3.selectbox('Subdivision', ['All / unassigned']+subdivisions)
block_df=b.filter(b['district']==district)
if subdiv!='All / unassigned': block_df=block_df.filter(block_df['subdivision']==subdiv)
block_names=sorted(block_df.get_column('block').to_list())
block=c4.selectbox('Block', ['District overview']+block_names)

st.markdown(f"### {block if block!='District overview' else district}")
if block=='District overview':
    total_blocks=block_df.height
    known_p=block_df.get_column('panchayat_count').drop_nulls().sum()
    known_v=block_df.get_column('village_count').drop_nulls().sum()
    a,bx,c=st.columns(3)
    a.metric('Blocks in view',total_blocks)
    bx.metric('Source-reported panchayats',int(known_p) if known_p is not None else '—')
    c.metric('Source-reported villages',int(known_v) if known_v is not None else '—')
    st.dataframe(block_df,width='stretch',hide_index=True)
    used=block_df.get_column('source_id').unique().to_list()
else:
    row=block_df.filter(block_df['block']==block)
    a,bx,c=st.columns(3)
    pc=row.get_column('panchayat_count')[0]; vc=row.get_column('village_count')[0]
    a.metric('Panchayats', 'Not reported' if pc is None else int(pc))
    bx.metric('Villages', 'Not reported' if vc is None else int(vc))
    c.metric('Quality',row.get_column('quality_class')[0])
    st.dataframe(row,width='stretch',hide_index=True)
    used=row.get_column('source_id').unique().to_list()

with st.expander('Evidence & provenance', expanded=True):
    st.dataframe(src.filter(src['source_id'].is_in(used)),width='stretch',hide_index=True)
    st.caption('Counts are source snapshots. A blank value means not reported/validated in the selected source, not zero.')

status_note("Verified map geometry is not bundled yet. JLA intentionally does not draw approximate or invented village/block coordinates. A map will activate when authoritative geometry is ingested and validated.")
