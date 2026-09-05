from __future__ import annotations
from pathlib import Path
import csv, yaml
from .modules import discover_modules
from .paths import DATA_DIR

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
    for m in discover_modules():
        if not m.get('_valid'): errors.extend([f"module {m.get('id')}: {e}" for e in m.get('_errors',[])])
    return errors
