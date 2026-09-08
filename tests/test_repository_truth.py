import json
from pathlib import Path

from jla.repository_truth import manifest_truth, module_status_truth, repository_truth_status


def test_live_repository_status_is_fail_closed():
    status = repository_truth_status()
    modules = status['modules']
    assert modules['roadmap_modules'] >= modules['implemented_modules']
    assert modules['implemented_modules'] == modules['complete_modules'] + modules['in_development_modules']
    assert modules['roadmap_modules'] == modules['implemented_modules'] + modules['planned_modules']
    assert 'core_geography' in modules['complete_ids']
    assert 'health_access' in modules['in_development_ids']
    assert status['manifest']['present'] is True
    assert isinstance(status['manifest']['is_current_inventory'], bool)


def test_manifest_truth_detects_unlisted_file(tmp_path: Path):
    (tmp_path / 'kept.txt').write_text('x', encoding='utf-8')
    (tmp_path / 'new.txt').write_text('y', encoding='utf-8')
    (tmp_path / 'MANIFEST.json').write_text(
        json.dumps({'generated': '2026-09-05', 'files': [{'path': 'kept.txt'}]}),
        encoding='utf-8',
    )
    result = manifest_truth(tmp_path)
    assert result['is_current_inventory'] is False
    assert result['unlisted_files'] == ['new.txt']
    assert result['missing_declared_files'] == []


def test_module_status_truth_keeps_planned_separate(tmp_path: Path):
    (tmp_path / 'config').mkdir()
    (tmp_path / 'modules' / 'core').mkdir(parents=True)
    (tmp_path / 'modules' / 'health').mkdir(parents=True)
    (tmp_path / 'config' / 'module_roadmap.yaml').write_text(
        'modules:\n  - [core, Core]\n  - [health, Health]\n  - [water, Water]\n',
        encoding='utf-8',
    )
    (tmp_path / 'modules' / 'core' / 'module.yaml').write_text(
        'id: core\nname: Core\nversion: 1.0.0\nstatus: complete\ndescription: Core\n',
        encoding='utf-8',
    )
    (tmp_path / 'modules' / 'health' / 'module.yaml').write_text(
        'id: health\nname: Health\nversion: 0.1.0\nstatus: active\ndescription: Health\n',
        encoding='utf-8',
    )
    result = module_status_truth(tmp_path)
    assert result['roadmap_modules'] == 3
    assert result['implemented_modules'] == 2
    assert result['complete_ids'] == ['core']
    assert result['in_development_ids'] == ['health']
    assert result['planned_ids'] == ['water']
