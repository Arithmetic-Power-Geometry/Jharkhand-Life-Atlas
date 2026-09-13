"""Fail-closed privacy helpers for source-schema and public-projection governance.

This module classifies column *names only*. It never inspects source row values.
The classification is deliberately conservative for fields that can expose a named
person or direct contact channel. Curators may read such fields inside governed,
ephemeral processing, but public projections must not select them unless a separate
rights/safety decision explicitly changes the publication contract.
"""
from __future__ import annotations

import re
from collections.abc import Iterable


PRIVACY_RULES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("email", ("email", "e mail")),
    (
        "telephone",
        (
            "telephone",
            "phone",
            "landline",
            "emergency num",
            "emergency number",
            "tollfree",
            "toll free",
            "helpline",
            "fax",
        ),
    ),
    ("mobile", ("mobile", "cell number", "cell no")),
    (
        "named_person",
        (
            "nodal person",
            "contact person",
            "contact name",
            "person name",
            "officer name",
            "nodal officer",
        ),
    ),
)


def normalized_header(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.casefold()).strip()


def privacy_risk_columns(header: Iterable[str]) -> list[dict[str, str]]:
    """Return conservative privacy findings using header names only."""
    findings: list[dict[str, str]] = []
    for column in header:
        normalized = normalized_header(str(column))
        for category, needles in PRIVACY_RULES:
            if any(needle in normalized for needle in needles):
                findings.append({"column": str(column), "category": category})
                break
    return findings


def public_projection_report(
    selected_columns: Iterable[str | None],
    *,
    source_header: Iterable[str],
) -> dict[str, object]:
    """Build a row-value-free audit report for a proposed public projection.

    The report is suitable for provenance receipts and repository-truth/Streamlit
    status surfaces because it contains only source column names and classifications.
    Publication is allowed by this *privacy-only* gate only when every selected
    column exists in the observed header and none is classified as privacy-risk.
    Other scientific, rights, geography and validation gates remain independent.
    """
    header = [str(c) for c in source_header]
    selected = [str(c) for c in selected_columns if c]
    selected_unique = list(dict.fromkeys(selected))
    header_set = set(header)

    missing = sorted(c for c in selected_unique if c not in header_set)
    risks = privacy_risk_columns(selected_unique)
    risk_names = {item["column"] for item in risks}
    safe = [c for c in selected_unique if c in header_set and c not in risk_names]

    return {
        "contract": "JLA_PRIVACY_PUBLIC_PROJECTION_V1",
        "classification_scope": "header_names_only",
        "row_values_inspected": False,
        "row_values_recorded": False,
        "selected_columns": selected_unique,
        "safe_selected_columns": safe,
        "privacy_risk_columns": risks,
        "missing_selected_columns": missing,
        "privacy_gate_passed": not risks and not missing,
    }


def assert_public_projection_columns_safe(
    selected_columns: Iterable[str | None],
    *,
    source_header: Iterable[str],
) -> None:
    """Reject any public projection that selects a privacy-risk source column.

    Sensitive columns may exist in the raw authoritative source. The gate concerns
    the configured columns that will be copied into a public/curated projection.
    This keeps raw-source acquisition possible while preventing accidental exposure.
    """
    report = public_projection_report(selected_columns, source_header=source_header)
    missing = report["missing_selected_columns"]
    if missing:
        raise ValueError(f"Configured projection columns are absent from source header: {missing}")

    risks = report["privacy_risk_columns"]
    if risks:
        details = ", ".join(f"{r['column']} ({r['category']})" for r in risks)
        raise ValueError(
            "Public projection selects privacy-risk source columns; remove them or complete an explicit rights/safety "
            f"review before publication: {details}"
        )
