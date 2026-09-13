#!/usr/bin/env python3
"""Aggregate-only audit for the provisional National Hospital Directory candidate.

This script deliberately emits no source rows and no values from privacy-risk columns.
It checks the governed schema, counts source-label Jharkhand coverage, measures missingness
for the candidate public projection, and diagnoses source geography identifier ambiguity.
It does not establish administrative equivalence or authorize publication.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Iterable


CONTRACT_NAME = "JLA_HEALTH_NHD_AGGREGATE_ROW_AUDIT_V1"


def _is_missing(value: object) -> bool:
    """Treat only empty/whitespace CSV cells as missing; never coerce them to zero."""
    return value is None or (isinstance(value, str) and value.strip() == "")


def _nonmissing_text(value: object) -> str | None:
    if _is_missing(value):
        return None
    return str(value).strip()


def _ambiguity_summary(rows: Iterable[dict[str, str]], label_field: str, id_field: str) -> dict:
    label_to_ids: dict[str, set[str]] = defaultdict(set)
    id_to_labels: dict[str, set[str]] = defaultdict(set)
    missing_pair_count = 0

    for row in rows:
        label = _nonmissing_text(row.get(label_field))
        source_id = _nonmissing_text(row.get(id_field))
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


def audit_rows(csv_path: Path, contract_path: Path) -> dict:
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    observed_columns = contract["observed_columns"]
    projection = contract["candidate_public_projection"]
    privacy_risk = set(contract["privacy_risk_columns"])

    assert not (privacy_risk & set(projection)), "privacy-risk column present in candidate public projection"
    assert contract["publication_allowed"] is False
    assert contract["geography_linkage_status"] == "unresolved"

    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        assert reader.fieldnames == observed_columns, "live CSV header differs from governed schema contract"
        rows = list(reader)

    assert len(rows) == contract["observed_data_row_count"], "live CSV row count differs from governed contract"

    # This is a source-label filter only. It must never be interpreted as proof that
    # source IDs equal LGD/Census/current administrative identifiers.
    jharkhand_rows = [
        row for row in rows
        if (_nonmissing_text(row.get("State")) or "").casefold() == "jharkhand"
    ]

    null_counts = {
        column: sum(1 for row in jharkhand_rows if _is_missing(row.get(column)))
        for column in projection
    }

    district_labels = sorted(
        {
            value
            for row in jharkhand_rows
            if (value := _nonmissing_text(row.get("District"))) is not None
        }
    )

    return {
        "contract": CONTRACT_NAME,
        "candidate_schema_contract": contract["contract"],
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
        "candidate_projection_null_counts": null_counts,
        "null_policy": "empty_or_whitespace_csv_cells_counted_as_missing; no zero filling performed",
        "state_identifier_audit": _ambiguity_summary(jharkhand_rows, "State", "State_ID"),
        "district_identifier_audit": _ambiguity_summary(jharkhand_rows, "District", "District_ID"),
        "privacy_risk_columns_read_for_output": [],
        "source_rows_emitted": False,
        "curated_dataset_emitted": False,
        "geography_linkage_status": "unresolved",
        "publication_allowed": False,
        "rules": [
            "aggregate audit output contains no source rows",
            "privacy-risk source values are not emitted",
            "missing values remain missing and are never converted to zero",
            "source-label matching does not establish cross-vintage administrative equivalence",
            "source identifiers remain uninterpreted until independently evidenced crosswalk records exist",
            "passing this audit does not authorize publication",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", type=Path, required=True)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    report = audit_rows(args.csv, args.contract)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
