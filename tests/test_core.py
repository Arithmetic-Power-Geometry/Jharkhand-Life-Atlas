from jla.validation import validate_core
from jla.modules import discover_modules

def test_core_integrity():
    assert validate_core() == []

def test_core_module_discovered():
    ids={m['id'] for m in discover_modules()}
    assert 'core_geography' in ids
