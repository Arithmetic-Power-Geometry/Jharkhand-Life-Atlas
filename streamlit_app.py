from __future__ import annotations
import streamlit as st
from jla.ui import configure, sidebar_footer

configure()

pages = {
    "Start": [
        st.Page("app_pages/home.py", title="Home", icon=":material/home:", default=True),
        st.Page("app_pages/explore.py", title="Explore places", icon=":material/location_on:"),
        st.Page("app_pages/modules.py", title="Browse modules", icon=":material/dashboard:"),
    ],
    "Research tools": [
        st.Page("app_pages/research.py", title="Download data", icon=":material/download:"),
        st.Page("app_pages/reports.py", title="Generate report", icon=":material/description:"),
        st.Page("app_pages/sources.py", title="Sources & methods", icon=":material/menu_book:"),
    ],
    "Administration": [
        st.Page("app_pages/admin.py", title="Admin", icon=":material/admin_panel_settings:"),
    ],
}

pg = st.navigation(pages, expanded=True)
sidebar_footer()
pg.run()
