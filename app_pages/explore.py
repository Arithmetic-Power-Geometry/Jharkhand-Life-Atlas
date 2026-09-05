import streamlit as st
from jla.ui import hero, badges, section_note
from jla.data import places, sources, optional_core_table

hero(
    "Explore places",
    "Explore verified Census 2011 geography, demographic baseline, current LGD administration, village amenities and temporal crosswalk evidence from one place-centred view.",
    eyebrow="Explore · Core Geography",
)

df = places()
src_df = sources()


def _height(data):
    if data is None:
        return 0
    try:
        return data.height
    except Exception:
        return len(data)


def _filter(data, column, value):
    if data is None or not value:
        return None
    try:
        if column not in data.columns:
            return None
        return data.filter(data[column].cast(str).str.strip_chars() == str(value).strip())
    except Exception:
        try:
            return [r for r in data if str(r.get(column, "")).strip() == str(value).strip()]
        except Exception:
            return None


def _value(record, key):
    v = record.get(key)
    return "" if v is None else str(v).strip()


def _hierarchy_value(record, field, target_level):
    current = _value(record, "place_type").lower()
    order = {"state": 0, "district": 1, "subdistrict": 2, "block": 3, "panchayat": 4, "village": 5, "town": 5}
    if field == "village" and current == "town":
        return "Not applicable to town records"
    value = _value(record, f"{field}_name")
    if value:
        return value
    if current in order and target_level in order and order[target_level] > order[current]:
        return f"Not applicable at {current} level"
    return "Not available in this verified record"


try:
    levels = df.get_column("place_type").unique().sort().to_list()
    top1, top2 = st.columns([1, 2])
    with top1:
        level = st.selectbox("Geographic level", levels, help="Verified levels available in the current published Core Geography release.")
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

    profile_tab, data_tab, admin_tab, evidence_tab, raw_tab = st.tabs([
        "Place profile", "Census & amenities", "Current administration", "Evidence & provenance", "Raw record"
    ])

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
            st.markdown(f"**State:** {_hierarchy_value(record, 'state', 'state')}")
            st.markdown(f"**District:** {_hierarchy_value(record, 'district', 'district')}")
            st.markdown(f"**Subdistrict:** {_hierarchy_value(record, 'subdistrict', 'subdistrict')}")
            st.markdown(f"**Block:** {_hierarchy_value(record, 'block', 'block')}")
            st.markdown(f"**Panchayat:** {_hierarchy_value(record, 'panchayat', 'panchayat')}")
            st.markdown(f"**Village:** {_hierarchy_value(record, 'village', 'village')}")
        section_note("Hierarchy fields distinguish 'not applicable at this geographic level' from genuinely unavailable verified values. JLA never fills missing hierarchy with guesses.")

        # Census child units provide context for higher-level pages.
        try:
            pid = _value(record, "place_id")
            children = df.filter(df["parent_place_id"] == pid)
            if children.height:
                st.markdown("#### Administrative units within this place")
                counts = children.group_by("place_type").len().sort("place_type")
                st.dataframe(counts, width="stretch", hide_index=True)
                with st.expander("View child units", expanded=False):
                    st.dataframe(children.select(["place_type", "name", "place_id"]), width="stretch", hide_index=True)
        except Exception:
            pass

    with data_tab:
        code = _value(record, "village_code") or (_value(record, "place_id").split("-")[-1] if _value(record, "place_type") in {"village", "town"} else "")
        district_code = _value(record, "district_code")

        demo = optional_core_table("village_demography_2011.csv")
        amenities = optional_core_table("village_amenities_2011.csv")

        demo_match = _filter(demo, "place_code", code)
        amen_match = _filter(amenities, "village_code", code) or _filter(amenities, "place_code", code)

        if _height(demo_match):
            st.markdown("#### Census 2011 demographic baseline")
            st.dataframe(demo_match, width="stretch", hide_index=True)
        elif _value(record, "place_type") in {"village", "town"}:
            st.info("No village/town demographic row is linked to this place in the current verified release.")
        else:
            st.info("Village-level Census demographic values are shown when an individual village or town is selected. Higher-level pages show their administrative structure rather than inventing aggregates.")

        if _height(amen_match):
            st.markdown("#### Census 2011 village amenities")
            st.dataframe(amen_match, width="stretch", hide_index=True)
        elif _value(record, "place_type") == "village":
            st.info("No DCHB village-amenities row is linked to this village in the current verified release.")

        if district_code and _value(record, "place_type") == "district":
            st.caption(f"District code {district_code}. Select a village to inspect village-level demographic and amenity observations.")

    with admin_tab:
        crosswalk = optional_core_table("census_lgd_temporal_crosswalk.csv")
        mdds = optional_core_table("census_mdds_crosswalk_2001_2011.csv")
        lgd_d = optional_core_table("lgd_districts_current.csv")
        lgd_sd = optional_core_table("lgd_subdistricts_current.csv")
        lgd_b = optional_core_table("lgd_blocks_current.csv")
        lgd_gp = optional_core_table("lgd_panchayats_current.csv")
        lgd_v = optional_core_table("lgd_villages_current.csv")

        st.markdown("#### Current LGD temporal view")
        st.caption("Current LGD records are intentionally separate from Census 2011. A crosswalk is displayed only where the published linkage supports it.")

        if _value(record, "place_type") == "district":
            dcode = _value(record, "district_code")
            shown = False
            for label, table, candidates in [
                ("District", lgd_d, ["districtCode", "district_code"]),
                ("Subdistricts", lgd_sd, ["districtCode", "district_code"]),
                ("Blocks", lgd_b, ["districtCode", "district_code"]),
            ]:
                match = None
                for col in candidates:
                    match = _filter(table, col, dcode)
                    if _height(match):
                        break
                if _height(match):
                    shown = True
                    st.markdown(f"**{label}: {_height(match):,} verified current row(s)**")
                    with st.expander(f"View {label.lower()} records", expanded=False):
                        st.dataframe(match, width="stretch", hide_index=True)
            if not shown:
                st.info("No current LGD rows are linked to this Census district code in the current display layer.")

        code = _value(record, "village_code") or (_value(record, "place_id").split("-")[-1] if _value(record, "place_type") in {"village", "town"} else "")
        cw_match = _filter(crosswalk, "census_2011_code", code) or _filter(crosswalk, "census_code", code)
        if _height(cw_match):
            st.markdown("#### Census 2011 ↔ current LGD linkage")
            st.dataframe(cw_match, width="stretch", hide_index=True)

        mdds_match = _filter(mdds, "village_code_2011", code) or _filter(mdds, "census_2011_code", code)
        if _height(mdds_match):
            st.markdown("#### Census 2001 ↔ 2011 MDDS linkage")
            st.dataframe(mdds_match, width="stretch", hide_index=True)

        if _value(record, "place_type") == "village" and not _height(cw_match) and not _height(mdds_match):
            st.caption("No verified historical/current crosswalk row is published for this village. Unmatched geography remains explicit rather than being guessed.")

    with evidence_tab:
        src_id = record.get("source_id")
        src = src_df.filter(src_df["source_id"] == src_id) if src_id else src_df.head(0)
        st.markdown("#### Source record")
        st.dataframe(src, width="stretch", hide_index=True)
        st.caption("The source registry records publisher, reference year, geographic resolution, retrieval method and redistribution status.")

        coverage = optional_core_table("source_coverage.csv")
        if _height(coverage):
            st.markdown("#### Module 1 source coverage")
            st.dataframe(coverage, width="stretch", hide_index=True)

    with raw_tab:
        st.dataframe(row, width="stretch", hide_index=True)
        st.caption("Raw curated place record exactly as stored in the current JLA release.")

except Exception as exc:
    st.warning("The structured explorer could not be rendered, so the current place table is shown directly.")
    st.dataframe(df, width="stretch", hide_index=True)
    st.caption(f"Explorer fallback: {type(exc).__name__}")
