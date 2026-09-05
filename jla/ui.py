import streamlit as st


def configure():
    st.set_page_config(
        page_title="Jharkhand Life Atlas",
        page_icon="🧭",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(
        """
        <style>
        :root {
            --jla-ink: #15352d;
            --jla-muted: #60736c;
            --jla-border: #dfe8e4;
            --jla-soft: #f5faf7;
            --jla-soft-2: #eef7f2;
            --jla-accent: #1f6f55;
        }
        .block-container {padding-top: 1.35rem; padding-bottom: 3rem; max-width: 1480px;}
        [data-testid="stSidebar"] {border-right: 1px solid var(--jla-border);}
        [data-testid="stSidebarNav"] {padding-top: .35rem;}
        h1, h2, h3 {letter-spacing: -.02em;}
        .jla-hero {
            padding: 1.65rem 1.8rem;
            border: 1px solid var(--jla-border);
            border-radius: 22px;
            background: linear-gradient(135deg, var(--jla-soft-2), #ffffff 62%);
            box-shadow: 0 8px 28px rgba(24, 70, 57, .06);
            margin-bottom: 1.15rem;
        }
        .jla-kicker {
            font-size: .76rem;
            letter-spacing: .12em;
            text-transform: uppercase;
            color: var(--jla-accent);
            font-weight: 800;
        }
        .jla-hero h1 {margin: .2rem 0 .45rem; color: var(--jla-ink); font-size: 2.25rem; line-height: 1.1;}
        .jla-muted {color: var(--jla-muted); font-size: 1.01rem; line-height: 1.55;}
        .jla-card {
            padding: 1.15rem 1.2rem;
            border: 1px solid var(--jla-border);
            border-radius: 16px;
            background: #ffffff;
            min-height: 150px;
            box-shadow: 0 3px 16px rgba(20, 55, 46, .04);
        }
        .jla-card-title {font-size: 1.02rem; font-weight: 760; color: var(--jla-ink); margin-bottom: .45rem;}
        .jla-card-copy {color: var(--jla-muted); line-height: 1.48; font-size: .94rem;}
        .jla-badge {
            display: inline-block;
            padding: .25rem .55rem;
            border-radius: 999px;
            background: var(--jla-soft-2);
            border: 1px solid var(--jla-border);
            color: var(--jla-accent);
            font-weight: 700;
            font-size: .76rem;
            margin-right: .35rem;
            margin-bottom: .35rem;
        }
        .jla-section-note {
            border-left: 4px solid var(--jla-accent);
            background: var(--jla-soft);
            border-radius: 0 12px 12px 0;
            padding: .8rem 1rem;
            color: var(--jla-muted);
            margin: .45rem 0 1rem;
        }
        div[data-testid="stMetric"] {
            background: #ffffff;
            border: 1px solid var(--jla-border);
            padding: .85rem 1rem;
            border-radius: 15px;
            box-shadow: 0 3px 14px rgba(20, 55, 46, .035);
        }
        div[data-testid="stMetricLabel"] {color: var(--jla-muted);}
        div[data-testid="stButton"] > button,
        div[data-testid="stDownloadButton"] > button {
            border-radius: 12px;
            min-height: 2.65rem;
            font-weight: 650;
        }
        div[data-testid="stDataFrame"] {border: 1px solid var(--jla-border); border-radius: 14px; overflow: hidden;}
        div[data-testid="stExpander"] {border-radius: 14px; border-color: var(--jla-border);}
        .jla-footer {color: #71817b; font-size: .77rem; line-height: 1.5;}
        @media (max-width: 700px) {
            .jla-hero {padding: 1.2rem; border-radius: 17px;}
            .jla-hero h1 {font-size: 1.7rem;}
            .block-container {padding-top: .8rem;}
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def hero(title, subtitle, eyebrow="Jharkhand Life Atlas"):
    st.markdown(
        f'<div class="jla-hero"><div class="jla-kicker">{eyebrow}</div>'
        f'<h1>{title}</h1><div class="jla-muted">{subtitle}</div></div>',
        unsafe_allow_html=True,
    )


def card(title, copy, icon=""):
    st.markdown(
        f'<div class="jla-card"><div class="jla-card-title">{icon} {title}</div>'
        f'<div class="jla-card-copy">{copy}</div></div>',
        unsafe_allow_html=True,
    )


def badges(items):
    html = "".join(f'<span class="jla-badge">{item}</span>' for item in items)
    st.markdown(html, unsafe_allow_html=True)


def section_note(text):
    st.markdown(f'<div class="jla-section-note">{text}</div>', unsafe_allow_html=True)


def sidebar_footer():
    with st.sidebar:
        st.divider()
        st.markdown("**JLA · Jharkhand Life Atlas**")
        st.caption("Evidence about people, places and access — connected at village level.")
        st.markdown('<div class="jla-footer">v1.0.0 · Provenance-first<br>Copyright (C) 2026 Mohammad Amir Khusru Akhtar · CC BY 4.0</div>', unsafe_allow_html=True)
