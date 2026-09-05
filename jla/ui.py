import html
import streamlit as st

VERSION='1.1.0'

def configure():
    st.set_page_config(page_title="Jharkhand Life Atlas", page_icon="🧭", layout="wide", initial_sidebar_state="expanded")
    st.markdown("""<style>
    :root{--jla:#145c48;--jla2:#287c64;--ink:#16332a;--muted:#60746d;--line:#d9e8e1;--soft:#f4faf7;--warn:#fff8e6}
    .block-container{padding-top:1.35rem;max-width:1480px}.jla-hero{padding:1.55rem 1.7rem;border:1px solid var(--line);border-radius:24px;background:linear-gradient(135deg,#edf8f3 0%,#ffffff 60%,#f6fbf8 100%);box-shadow:0 10px 35px rgba(19,85,66,.07);margin-bottom:1rem}
    .jla-kicker{font-size:.78rem;letter-spacing:.13em;text-transform:uppercase;color:var(--jla2);font-weight:800}.jla-hero h1{color:var(--ink);font-size:2.25rem}.jla-muted{color:var(--muted);font-size:1.05rem;max-width:1050px}.jla-card{padding:1.1rem;border:1px solid var(--line);border-radius:18px;background:white;min-height:135px;box-shadow:0 5px 20px rgba(19,85,66,.04)}
    .jla-pill{display:inline-block;padding:.3rem .65rem;border-radius:999px;background:#eaf7f1;color:#155d49;font-size:.78rem;font-weight:700;margin:.15rem .25rem .15rem 0}.jla-pill-warn{background:#fff3d5;color:#7a5710}.jla-note{padding:.9rem 1rem;border-left:4px solid var(--jla2);background:var(--soft);border-radius:10px;color:var(--ink)}
    div[data-testid="stMetric"]{background:white;border:1px solid var(--line);padding:.75rem 1rem;border-radius:16px;box-shadow:0 4px 16px rgba(19,85,66,.04)}
    [data-testid="stSidebar"]{border-right:1px solid #e3eee9}.stButton>button,.stDownloadButton>button{border-radius:12px}.stDataFrame{border:1px solid var(--line);border-radius:12px;overflow:hidden}
    </style>""", unsafe_allow_html=True)

def hero(title, subtitle, badges=None):
    badges = badges or []
    pills=''.join(f'<span class="jla-pill">{html.escape(str(b))}</span>' for b in badges)
    st.markdown(f'<div class="jla-hero"><div class="jla-kicker">Jharkhand Life Atlas · v{VERSION}</div><h1 style="margin:.18rem 0 .45rem">{html.escape(title)}</h1><div class="jla-muted">{html.escape(subtitle)}</div><div style="margin-top:.7rem">{pills}</div></div>', unsafe_allow_html=True)

def status_note(text): st.markdown(f'<div class="jla-note">{text}</div>', unsafe_allow_html=True)

def sidebar_footer():
    with st.sidebar:
        st.divider(); st.caption(f"JLA v{VERSION} · Non-partisan · Provenance-first")
        st.caption("Copyright (C) 2026 Mohammad Amir Khusru Akhtar · CC BY 4.0 original JLA material")
