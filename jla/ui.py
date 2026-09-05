import streamlit as st

def configure():
    st.set_page_config(page_title="Jharkhand Life Atlas", page_icon="🧭", layout="wide", initial_sidebar_state="expanded")
    st.markdown("""<style>
      .block-container{padding-top:1.5rem;max-width:1450px}.jla-hero{padding:1.25rem 1.4rem;border:1px solid #d8e6df;border-radius:18px;background:linear-gradient(135deg,#f4faf7,#ffffff)}
      .jla-kicker{font-size:.82rem;letter-spacing:.08em;text-transform:uppercase;color:#477466;font-weight:700}.jla-muted{color:#5e726b}.jla-card{padding:1rem;border:1px solid #dfe9e4;border-radius:14px;background:white;min-height:135px}
      div[data-testid="stMetric"]{background:white;border:1px solid #dfe9e4;padding:.7rem 1rem;border-radius:14px}
    </style>""", unsafe_allow_html=True)

def hero(title, subtitle):
    st.markdown(f'<div class="jla-hero"><div class="jla-kicker">Jharkhand Life Atlas</div><h1 style="margin:.15rem 0 .4rem">{title}</h1><div class="jla-muted">{subtitle}</div></div>', unsafe_allow_html=True)

def sidebar_footer():
    with st.sidebar:
        st.divider(); st.caption("JLA v1.0.0 · Non-partisan · Provenance-first")
        st.caption("Copyright (C) 2026 Mohammad Amir Khusru Akhtar · CC BY 4.0")
