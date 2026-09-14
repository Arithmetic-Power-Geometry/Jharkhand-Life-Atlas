#!/usr/bin/env python3
"""Aggregate-only audit for the provisional National Hospital Directory candidate.

This script deliberately emits no source rows and no values from privacy-risk columns.
It checks the governed schema, counts source-label Jharkhand coverage, measures missingness
for the candidate public projection, diagnoses source geography identifier ambiguity, and
summarizes parse quality for governed numeric candidate fields. Numeric quality output is
aggregate-only: it never emits rejected source values. Missingness is governed by the
separate semantic contract so CI cannot silently diverge from the scientific null policy.
It also separates superficial label-normalization collisions from identifier ambiguity.
It does not establish administrative equivalence or authorize publication.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Iterable


CONTRACT_NAME = "JLA_HEALTH_NHD_AGGREGATE_ROW_AUDIT_V3"
SEMANTIC_CONTRACT_NAME = "JLA_HEALTH_NHD_SEMANTIC_CONTRACT_V2"


def _missing_token_set(tokens: Iterable[object]) -> set[str]:
    """Normalize governed textual missing tokens without inventing new sentinels."""
    return {
        str(token).strip().casefold()
        for token in tokens
        if token is not None and str(token).strip() != ""
    }


def _is_missing(value: object, missing_tokens: set[str]) -> bool:
    """Apply governed missing tokens; never coerce a missing value to zero."""
    if value is None:
        return True
    if isinstance(value, str):
        text = value.strip()
        if text == "":
            return True
        return text.casefold() in missing_tokens
    return False


def _nonmissing_text(value: object, missing_tokens: set[str]) -> str | None:
    if _is_missing(value, missing_tokens):
        return None
    return str(value).strip()


def _numeric_quality_summary(
    rows: Iterable[dict[str, str]],
    fields: Iterable[str],
    missing_tokens: set[str],
) -> dict[str, dict[str, int | bool | str]]:
    """Summarize numeric parse quality without exposing source values.

    NHD candidate numeric fields are count/year-like fields. A scientifically eligible
    observed value must therefore parse as a finite, non-negative integer. Anything else
    remains unresolved and must become null in a future curated layer unless authoritative
    documentation establishes another interpretation.
    """
    output: dict[str, dict[str, int | bool | str]] = {}
    for field in fields:
        summary: dict[str, int | bool | str] = {
            "missing_count": 0,
            "observed_nonmissing_count": 0,
            "parseable_nonnegative_integer_count": 0,
            "zero_count": 0,
            "negative_count": 0,
            "noninteger_numeric_count": 0,
            "unparsable_count": 0,
            "raw_values_emitted": False,
            "future_curated_failed_parse_representation": "null",
        }
        for row in rows:
            value = row.get(field)
            if _is_missing(value, missing_tokens):
                summary["missing_count"] += 1  # type: ignore[operator]
                continue
            summary["observed_nonmissing_count"] += 1  # type: ignore[operator]
            text = str(value).strip()
            try:
                parsed = Decimal(text)
            except (InvalidOperation, ValueError):
                summary["unparsable_count"] += 1  # type: ignore[operator]
                continue
            if not parsed.is_finite():
                summary["unparsable_count"] += 1  # type: ignore[operator]
                continue
            if parsed < 0:
                summary["negative_count"] += 1  # type: ignore[operator]
                continue
            if parsed != parsed.to_integral_value():
                summary["noninteger_numeric_count"] += 1  # type: ignore[operator]
                continue
            summary["parseable_nonnegative_integer_count"] += 1  # type: ignore[operator]
            if parsed == 0:
                summary["zero_count"] += 1  # type: ignore[operator]
        output[field] = summary
    return output


def _ambiguity_summary(
    rows: Iterable[dict[str, str]],
    label_field: str,
    id_field: str,
    missing_tokens: set[str],
) -> dict:
    label_to_ids: dict[str, set[str]] = defaultdict(set)
    id_to_labels: dict[str, set[str]] = defaultdict(set)
    missing_pair_count = 0

    for row in rows:
        label = _nonmissing_text(row.get(label_field), missing_tokens)
        source_id = _nonmissing_text(row.get(id_field), missing_tokens)
        if label is None or source_id is None:
            missing_pair_count += 1
            continue
        label_to_ids[label].add(source_id)
        id_to_labels[source_id].add(label)

    labels_with_multiple_ids = sorted(label for label, ids in label_to_ids.items() if len(ids) > 1)
    ids_with_multiple_labels = sorted(source_id for source_id, labels in id_to_labels.items() if len(labels) > 1)

    return {
        "label_field": label_field,
        "id_field": id_field,
        "observed_label_count": len(label_to_ids),
        "observed_id_count": len(id_to_labels),
        "missing_label_or_id_pair_count": missing_pair_count,
        "labels_with_multiple_ids_count": len(labels_with_multiple_ids),
        "ids_with_multiple_labels_count": len(ids_with_multiple_labels),
        "labels_with_multiple_ids": labels_with_multiple_ids,
        "ids_with_multiple_labels": ids_with_multiple_labels,
        "internally_one_to_one": (
            missing_pair_count == 0
            and not labels_with_multiple_ids
            and not ids_with_multiple_labels
        ),
        "administrative_equivalence_established": False,
    }


def _label_normalization_audit(
    rows: Iterable[dict[str, str]],
    label_field: str,
    missing_tokens: set[str],
) -> dict:
    """Report trim+casefold collisions without treating them as admin equivalence."""
    normalized_to_raw: dict[str, set[str]] = defaultdict(set)
    missing_count = 0
    for row in rows:
        raw = _nonmissing_text(row.get(label_field), missing_tokens)
        if raw is None:
            missing_count += 1
            continue
        normalized_to_raw[raw.casefold()].add(raw)

    collisions = {
        normalized: sorted(raw_values)
        for normalized, raw_values in sorted(normalized_to_raw.items())
        if len(raw_values) > 1
    }
    return {
        "label_field": label_field,
        "normalization": "strip_then_casefold",
        "raw_distinct_label_count": sum(len(values) for values in normalized_to_raw.values()),
        "normalized_distinct_label_count": len(normalized_to_raw),
        "missing_label_count": missing_count,
        "normalization_collision_count": len(collisions),
        "normalization_collisions": collisions,
        "administrative_equivalence_established": False,
        "rule": "normalization may diagnose spelling/case variants but cannot establish cross-vintage administrative equivalence",
    }


def audit_rows(csv_path: Path, contract_path: Path, semantic_contract_path: Path) -> dict:
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    semantic = json.loads(semantic_contract_path.read_text(encoding="utf-8"))

    assert semantic["contract"] == SEMANTIC_CONTRACT_NAME
    assert semantic["publication_allowed"] is False
    assert semantic["row_level_curated_dataset_emitted"] is False
    assert semantic["null_policy"]["canonical_missing_representation"] is None
    assert semantic["null_policy"]["missing_to_zero_allowed"] is False
    assert semantic["numeric_cleaning_rules"]["parse_only_when_unambiguous"] is True
    assert semantic["numeric_cleaning_rules"]["negative_counts_allowed"] is False
    assert semantic["numeric_cleaning_rules"]["failed_parse_becomes_null"] is True
    assert semantic["numeric_cleaning_rules"]["no_imputation"] is True

    governed_missing_tokens = list(semantic["null_policy"]["source_missing_tokens"])
    missing_tokens = _missing_token_set(governed_missing_tokens)

    observed_columns = contract["observed_columns"]
    projection = contract["candidate_public_projection"]
    privacy_risk = set(contract["privacy_risk_columns"])
    numeric_fields = list(semantic["field_groups"]["numeric_candidate_fields"])

    assert not (privacy_risk & set(projection)), "privacy-risk column present in candidate public projection"
    assert set(numeric_fields).issubset(set(observed_columns)), "governed numeric field absent from observed schema"
    assert contract["publication_allowed"] is False
    assert contract["geography_linkage_status"] == "unresolved"

    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        assert reader.fieldnames == observed_columns, "live CSV header differs from governed schema contract"
        rows = list(reader)

    assert len(rows) == contract["observed_data_row_count"], "live CSV row count differs from governed contract"

    jharkhand_rows = [
        row for row in rows
        if (_nonmissing_text(row.get("State"), missing_tokens) or "").casefold() == "jharkhand"
    ]

    null_counts = {
        column: sum(1 for row in jharkhand_rows if _is_missing(row.get(column), missing_tokens))
        for column in projection
    }

    district_labels = sorted(
        {
            value
            for row in jharkhand_rows
            if (value := _nonmissing_text(row.get("District"), missing_tokens)) is not None
        }
    )

    return {
        "contract": CONTRACT_NAME,
        "candidate_schema_contract": contract["contract"],
        "semantic_contract": semantic["contract"],
        "source_sha256_expected": contract["source_sha256"],
        "source_row_count_verified": len(rows),
        "source_column_count_verified": len(observed_columns),
        "jharkhand_source_label_match": {
            "field": "State",
            "match_rule": "strip_then_casefold_equals_jharkhand",
            "row_count": len(jharkhand_rows),
            "establishes_administrative_equivalence": False,
        },
        "jharkhand_distinct_district_label_count": len(district_labels),
        "jharkhand_distinct_district_labels": district_labels,
        "district_label_normalization_audit": _label_normalization_audit(
            jharkhand_rows, "District", missing_tokens
        ),
        "candidate_projection_null_counts": null_counts,
        "numeric_candidate_quality": _numeric_quality_summary(
            jharkhand_rows, numeric_fields, missing_tokens
        ),
        "numeric_quality_rule": "aggregate parse diagnostics only; invalid/unresolved values are not emitted and cannot support indicators",
        "source_missing_tokens": governed_missing_tokens,
        "canonical_missing_representation": None,
        "missing_to_zero_allowed": False,
        "zero_is_observed_value_only": semantic["numeric_cleaning_rules"]["zero_is_observed_value_only"],
        "null_policy": "missing tokens are governed by the NHD semantic contract; no zero filling performed",
        "state_identifier_audit": _ambiguity_summary(
            jharkhand_rows, "State", "State_ID", missing_tokens
        ),
        "district_identifier_audit": _ambiguity_summary(
            jharkhand_rows, "District", "District_ID", missing_tokens
        ),
        "privacy_risk_columns_read_for_output": [],
        "source_rows_emitted": False,
        "curated_dataset_emitted": False,
        "geography_linkage_status": "unresolved",
        "publication_allowed": False,
        "rules": [
            "aggregate audit output contains no source rows",
            "privacy-risk source values are not emitted",
            "governed missing tokens remain null and are never converted to zero",
            "zero is counted as an observed value only",
            "numeric candidate quality is aggregate-only and does not emit rejected source values",
            "unparsable, negative, or non-integer numeric candidates cannot support derived indicators",
            "label normalization is diagnostic only and does not establish administrative equivalence",
            "source-label matching does not establish cross-vintage administrative equivalence",
            "source identifiers remain uninterpreted until independently evidenced crosswalk records exist",
            "passing this audit does not authorize publication",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", type=Path, required=True)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--semantic-contract", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    report = audit_rows(args.csv, args.contract, args.semantic_contract)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
