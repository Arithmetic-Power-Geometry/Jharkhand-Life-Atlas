import streamlit as st
from jla.ui import hero, badges, section_note
from jla.data import places, sources

hero(
    "Explore places",
    "Choose a geographic level and place, then inspect its identifiers, hierarchy and source evidence. This page will automatically become richer as village, block and panchayat records are added.",
    eyebrow="Explore · Core Geography",
)

df = places()
src_df = sources()

try:
    levels = df.get_column("place_type").unique().sort().to_list()
    top1, top2 = st.columns([1, 2])
    with top1:
        level = st.selectbox("Geographic level", levels, help="Current release contains verified district records; more levels will appear as authoritative data are added.")
    sub = df.filter(df["place_type"] == level)
    names = sub.get_column("name").sort().to_list()
    with top2:
        name = st.selectbox("Place", names)

    row = sub.filter(sub["name"] == name)
    record = row.to_dicts()[0]

    badges([
        f"{record.get('place_type', 'place').title()}",
        f"Quality {record.get('quality_class', '—')}",
        str(record.get("record_status", "record")),
        f"Valid from {record.get('valid_from', '—')}",
    ])

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Place", record.get("name", "—"))
    c2.metric("District code", record.get("district_code") or "—")
    c3.metric("State code", record.get("state_code") or "—")
    c4.metric("Source", record.get("source_id") or "—")

    profile_tab, evidence_tab, raw_tab = st.tabs(["Place profile", "Evidence & provenance", "Raw record"])

    with profile_tab:
        left, right = st.columns(2)
        with left:
            st.markdown("#### Identity")
            st.markdown(f"**JLA place ID:** `{record.get('place_id', '—')}`")
            st.markdown(f"**Name:** {record.get('name', '—')}")
            st.markdown(f"**Type:** {record.get('place_type', '—')}")
            st.markdown(f"**Parent place ID:** `{record.get('parent_place_id') or '—'}`")
        with right:
            st.markdown("#### Administrative hierarchy")
            st.markdown(f"**State:** {record.get('state_name') or '—'}")
            st.markdown(f"**District:** {record.get('district_name') or '—'}")
            st.markdown(f"**Subdistrict:** {record.get('subdistrict_name') or 'Not yet published'}")
            st.markdown(f"**Block:** {record.get('block_name') or 'Not yet published'}")
            st.markdown(f"**Panchayat:** {record.get('panchayat_name') or 'Not yet published'}")
            st.markdown(f"**Village:** {record.get('village_name') or 'Not yet published'}")
        section_note("Blank hierarchy fields mean the value is not present in the verified current release. JLA does not convert missing fields into guessed values.")

    with evidence_tab:
        src_id = record.get("source_id")
        src = src_df.filter(src_df["source_id"] == src_id) if src_id else src_df.head(0)
        st.markdown("#### Source record")
        st.dataframe(src, width="stretch", hide_index=True)
        st.caption("The source registry records publisher, reference year, geographic resolution, retrieval method and redistribution status.")

    with raw_tab:
        st.dataframe(row, width="stretch", hide_index=True)
        st.caption("Raw curated place record exactly as stored in the current JLA release.")

except Exception as exc:
    st.warning("The structured explorer could not be rendered, so the current place table is shown directly.")
    st.dataframe(df, width="stretch", hide_index=True)
    st.caption(f"Explorer fallback: {type(exc).__name__}")
