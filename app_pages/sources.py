import streamlit as st
from jla.ui import hero, section_note
from jla.data import sources, variables, source_coverage

hero(
    "Sources, methods & responsible use",
    "Trace JLA evidence from published values back to authoritative sources, licensing decisions, temporal context and publication safeguards.",
)

src = sources()

t1, t2, t3, t4 = st.tabs([
    "Coverage audit",
    "Source registry",
    "Governance gate",
    "Variable registry",
])

with t1:
    st.markdown("### Module evidence coverage")
    st.caption(
        "INGESTED means records are published in JLA. A verified source is not automatically a reusable source: publication still depends on rights, privacy, sensitivity and validation checks."
    )
    st.dataframe(source_coverage(), width="stretch", hide_index=True)

with t2:
    st.markdown("### Source registry")
    st.dataframe(src, width="stretch", hide_index=True)
    st.caption(
        "Each source carries its publisher, period, geographic resolution, reuse posture, attribution requirement and governance review status."
    )

with t3:
    st.markdown("### Mandatory publication gate")
    st.markdown(
        "A dataset is not publishable merely because it is visible online. Before a factual value enters JLA, the source must pass checks for **authority, provenance, rights, attribution, privacy, sensitivity, geographic disclosure, scientific integrity, temporal integrity and validation**."
    )

    st.markdown("#### Publication classes")
    st.dataframe(
        {
            "Class": [
                "OPEN",
                "OPEN_WITH_ATTRIBUTION",
                "DERIVED_ONLY",
                "AGGREGATE_ONLY",
                "RESTRICTED",
                "DO_NOT_PUBLISH",
            ],
            "JLA meaning": [
                "Explicit open licence permits redistribution and reuse.",
                "Reuse is permitted subject to acknowledgement or stated conditions.",
                "Source may inform analysis, but raw redistribution rights are not sufficiently clear.",
                "Only approved aggregation/generalisation may be published.",
                "Access or reuse is limited by permission, contract or confidentiality.",
                "Rights, privacy, safety or integrity risk prevents public publication.",
            ],
        },
        width="stretch",
        hide_index=True,
    )

    st.markdown("#### Privacy and sensitive evidence")
    st.markdown(
        "JLA is **place-centred, not person-centred**. Public releases should not expose private individuals, identity numbers, contact details, medical records, identifiable beneficiaries/victims, or unsafe household-level locations. Wildlife data are also reviewed for ecological disclosure risk; real-time or operationally sensitive protected-wildlife locations should not be published."
    )

    st.markdown("#### Interpretation rule")
    st.info(
        "JLA measures data-defined conditions. It does not score political parties, elected representatives or governments, and spatial association must not be interpreted as attribution of political responsibility."
    )

    section_note(
        "The full project policy is maintained in docs/DATA_GOVERNANCE.md. Unclear rights default to a conservative publication class until verified."
    )

with t4:
    st.dataframe(variables(), width="stretch", hide_index=True)

st.info(
    "JLA keeps Census 2011 geography separate from current Jharkhand administrative/LGD geography. Similar names do not imply identical geographic entities or time periods."
)
st.warning(
    "Source inclusion does not transfer third-party copyright or licence. JLA's own licence never overrides the source provider's terms."
)
st.caption(
    "Jharkhand Life Atlas is an independent, non-partisan research infrastructure and is not affiliated with or endorsed by the Government of Jharkhand, Government of India, or source organisations."
)
