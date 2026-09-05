from __future__ import annotations
import streamlit as st
from jla.ui import configure, sidebar_footer

configure()

pages = {
    "Discover": [
        st.Page("app_pages/home.py", title="Home", icon=":material/home:", default=True),
        st.Page("app_pages/explore.py", title="Explore places", icon=":material/travel_explore:"),
        st.Page("app_pages/modules.py", title="Modules", icon=":material/widgets:"),
    ],
    "Use the evidence": [
        st.Page("app_pages/research.py", title="Research & download", icon=":material/science:"),
        st.Page("app_pages/reports.py", title="Generate report", icon=":material/article:"),
        st.Page("app_pages/sources.py", title="Sources & methods", icon=":material/library_books:"),
    ],
    "Manage": [
        st.Page("app_pages/admin.py", title="Admin", icon=":material/admin_panel_settings:"),
    ],
}
pg = st.navigation(pages, expanded=True)
sidebar_footer()
pg.run()
