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
    ("telephone", ("telephone", "phone", "landline")),
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
    header = [str(c) for c in source_header]
    selected = {str(c) for c in selected_columns if c}
    missing = selected.difference(header)
    if missing:
        raise ValueError(f"Configured projection columns are absent from source header: {sorted(missing)}")

    risks = privacy_risk_columns(selected)
    if risks:
        details = ", ".join(f"{r['column']} ({r['category']})" for r in risks)
        raise ValueError(
            "Public projection selects privacy-risk source columns; remove them or complete an explicit rights/safety "
            f"review before publication: {details}"
        )
