from __future__ import annotations
import csv
from .modules import discover_modules
from .paths import DATA_DIR, REGISTRY_DIR

CORE = DATA_DIR / 'curated' / 'core_geography'

def _rows(path):
    with path.open(encoding='utf-8', newline='') as f:
        return list(csv.DictReader(f))

def validate_core() -> list[str]:
    errors=[]
    required_files=['places.csv','current_blocks.csv','state_facts_2011.csv','census_pca_catalog.csv','reconciliation.csv']
    for name in required_files:
        if not (CORE/name).exists(): errors.append(f'Missing {name}')
    if errors: return errors

    places=_rows(CORE/'places.csv')
    required={'place_id','place_type','name','parent_place_id','source_id','official_code_status','record_status'}
    if not places: errors.append('places.csv has no rows')
    elif not required <= set(places[0]): errors.append('places.csv missing required columns')
    ids=[r.get('place_id','') for r in places]
    if len(ids)!=len(set(ids)): errors.append('duplicate place_id values')
    if any(not x for x in ids): errors.append('blank place_id')
    expected={'state':1,'division':5,'district':24,'subdivision':45,'block':264}
    counts={k:sum(r.get('place_type')==k for r in places) for k in expected}
    for k,v in expected.items():
        if counts.get(k)!=v: errors.append(f'expected {v} {k} rows, found {counts.get(k)}')
    valid_ids=set(ids)|{'IND'}
    for r in places:
        if r.get('parent_place_id') and r['parent_place_id'] not in valid_ids:
            errors.append(f"invalid parent_place_id {r['parent_place_id']} for {r['place_id']}")
            break

    blocks=_rows(CORE/'current_blocks.csv')
    if len(blocks)!=264: errors.append(f'expected 264 block snapshot rows, found {len(blocks)}')
    block_keys=[(r.get('district'),r.get('block')) for r in blocks]
    if len(block_keys)!=len(set(block_keys)): errors.append('duplicate district+block rows')
    if any(not d or not b for d,b in block_keys): errors.append('blank district/block in current_blocks.csv')
    if not any(r.get('district')=='Latehar' and r.get('block')=='Saryu' for r in blocks): errors.append('Latehar/Saryu block missing')

    pca=_rows(CORE/'census_pca_catalog.csv')
    if len(pca)!=24: errors.append(f'expected 24 PCA catalog rows, found {len(pca)}')
    if any(r.get('ingestion_status')!='catalog_verified_family_raw_file_not_bundled' for r in pca):
        errors.append('unexpected PCA ingestion status')

    rec=_rows(CORE/'reconciliation.csv')
    if {r.get('metric') for r in rec}!={'blocks','panchayats','villages','subdivisions'}:
        errors.append('reconciliation metrics incomplete')

    src=_rows(REGISTRY_DIR/'sources.csv')
    known={r.get('source_id') for r in src}
    used={r.get('source_id') for r in places+blocks+_rows(CORE/'state_facts_2011.csv') if r.get('source_id')}
    unknown=sorted(used-known)
    if unknown: errors.append('unregistered source IDs: '+', '.join(unknown))

    for m in discover_modules():
        if not m.get('_valid'): errors.extend([f"module {m.get('id')}: {e}" for e in m.get('_errors',[])])
    return errors
