from __future__ import annotations
from pathlib import Path
import csv, yaml
from .modules import discover_modules
from .paths import DATA_DIR

VALID_PUBLICATION_CLASSES = {
    'OPEN',
    'OPEN_WITH_ATTRIBUTION',
    'DERIVED_ONLY',
    'AGGREGATE_ONLY',
    'RESTRICTED',
    'DO_NOT_PUBLISH',
}

SOURCE_GOVERNANCE_FIELDS = {
    'source_id',
    'title',
    'publisher',
    'url',
    'reference_year',
    'license_or_policy',
    'redistribution_status',
    'publication_class',
    'license_review_status',
    'personal_data_risk',
    'sensitivity_risk',
    'attribution_requirement',
    'governance_review_status',
}


def _validate_source_governance(root: Path) -> list[str]:
    errors: list[str] = []
    path = root / 'registry' / 'sources.csv'
    if not path.exists():
        return ['Missing registry/sources.csv']

    with path.open(encoding='utf-8', newline='') as f:
        rows = list(csv.DictReader(f))

    if not rows:
        return ['registry/sources.csv has no rows']

    columns = set(rows[0])
    missing_columns = SOURCE_GOVERNANCE_FIELDS - columns
    if missing_columns:
        errors.append(
            'registry/sources.csv missing governance columns: ' + ', '.join(sorted(missing_columns))
        )
        return errors

    seen: set[str] = set()
    for i, row in enumerate(rows, start=2):
        sid = (row.get('source_id') or '').strip()
        if not sid:
            errors.append(f'registry/sources.csv row {i}: blank source_id')
        elif sid in seen:
            errors.append(f'registry/sources.csv row {i}: duplicate source_id {sid}')
        seen.add(sid)

        for field in SOURCE_GOVERNANCE_FIELDS:
            if not (row.get(field) or '').strip():
                errors.append(f'registry/sources.csv row {i} ({sid or "unknown"}): blank {field}')

        publication_class = (row.get('publication_class') or '').strip()
        if publication_class and publication_class not in VALID_PUBLICATION_CLASSES:
            errors.append(
                f'registry/sources.csv row {i} ({sid or "unknown"}): invalid publication_class {publication_class}'
            )

    return errors


def validate_core() -> list[str]:
    errors=[]
    p=DATA_DIR/'curated'/'core_geography'/'places.csv'
    if not p.exists(): return ["Missing places.csv"]
    with p.open(encoding='utf-8',newline='') as f:
        rows=list(csv.DictReader(f))
    required={'place_id','place_type','name','state_name','source_id'}
    if not rows: errors.append('places.csv has no rows')
    elif not required <= set(rows[0]): errors.append('places.csv missing required columns')
    ids=[r.get('place_id') for r in rows]
    if len(ids)!=len(set(ids)): errors.append('duplicate place_id values')
    if any(not x for x in ids): errors.append('blank place_id')

    root = Path(__file__).resolve().parents[1]
    errors.extend(_validate_source_governance(root))

    for m in discover_modules():
        if not m.get('_valid'): errors.extend([f"module {m.get('id')}: {e}" for e in m.get('_errors',[])])
    return errors
