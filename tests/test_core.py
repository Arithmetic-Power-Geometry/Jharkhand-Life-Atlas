import csv
from pathlib import Path
from jla.validation import validate_core
from jla.modules import discover_modules
from jla.paths import DATA_DIR, REGISTRY_DIR

CORE=DATA_DIR/'curated'/'core_geography'

def rows(name):
    with (CORE/name).open(encoding='utf-8',newline='') as f: return list(csv.DictReader(f))

def test_core_integrity():
    assert validate_core() == []

def test_core_module_discovered():
    assert 'core_geography' in {m['id'] for m in discover_modules()}

def test_hierarchy_counts_and_saryu():
    p=rows('places.csv')
    counts={t:sum(r['place_type']==t for r in p) for t in ['state','division','district','subdivision','block']}
    assert counts == {'state':1,'division':5,'district':24,'subdivision':45,'block':264}
    b=rows('current_blocks.csv')
    assert len(b)==264
    assert any(r['district']=='Latehar' and r['block']=='Saryu' for r in b)

def test_pca_catalog_and_conflict_audit():
    assert len(rows('census_pca_catalog.csv'))==24
    rec={r['metric']:r for r in rows('reconciliation.csv')}
    assert rec['blocks']['status']=='reconciled'
    assert rec['panchayats']['status']=='conflict_preserved'
    assert rec['villages']['status']=='conflict_preserved'
    assert rec['subdivisions']['status']=='temporal_conflict'

def test_all_used_sources_registered():
    with (REGISTRY_DIR/'sources.csv').open(encoding='utf-8',newline='') as f: known={r['source_id'] for r in csv.DictReader(f)}
    used=set()
    for n in ['places.csv','current_blocks.csv','state_facts_2011.csv']:
        used|={r['source_id'] for r in rows(n) if r.get('source_id')}
    assert used <= known
