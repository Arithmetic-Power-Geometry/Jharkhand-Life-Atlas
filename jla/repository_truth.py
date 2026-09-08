from __future__ import annotations

import json
from pathlib import Path

import yaml

from .modules import discover_modules


IGNORED_PARTS = {'.git', '.pytest_cache', '__pycache__', '.venv', 'venv'}


def _root(root: Path | None = None) -> Path:
    return root or Path(__file__).resolve().parents[1]


def _roadmap(root: Path) -> list[tuple[str, str]]:
    path = root / 'config' / 'module_roadmap.yaml'
    if not path.exists():
        return []
    raw = (yaml.safe_load(path.read_text(encoding='utf-8')) or {}).get('modules', [])
    out: list[tuple[str, str]] = []
    for entry in raw:
        if isinstance(entry, (list, tuple)) and len(entry) >= 2:
            out.append((str(entry[0]), str(entry[1])))
        elif isinstance(entry, dict) and entry.get('id'):
            out.append((str(entry['id']), str(entry.get('name') or entry['id'])))
    return out


def module_status_truth(root: Path | None = None) -> dict:
    base = _root(root)
    modules = discover_modules(base / 'modules')
    by_id = {str(m.get('id')): m for m in modules if m.get('id')}
    roadmap = _roadmap(base)
    if not roadmap:
        roadmap = [(module_id, str(meta.get('name') or module_id)) for module_id, meta in by_id.items()]

    complete = [module_id for module_id, _ in roadmap if by_id.get(module_id, {}).get('status') == 'complete']
    in_development = [
        module_id for module_id, _ in roadmap
        if module_id in by_id and by_id[module_id].get('status') != 'complete'
    ]
    planned = [module_id for module_id, _ in roadmap if module_id not in by_id]
    return {
        'roadmap_modules': len(roadmap),
        'implemented_modules': len([module_id for module_id, _ in roadmap if module_id in by_id]),
        'complete_modules': len(complete),
        'in_development_modules': len(in_development),
        'planned_modules': len(planned),
        'complete_ids': complete,
        'in_development_ids': in_development,
        'planned_ids': planned,
    }


def manifest_truth(root: Path | None = None) -> dict:
    base = _root(root)
    path = base / 'MANIFEST.json'
    if not path.exists():
        return {
            'present': False,
            'generated': None,
            'declared_files': 0,
            'actual_files': 0,
            'unlisted_files': [],
            'missing_declared_files': [],
            'is_current_inventory': False,
        }

    payload = json.loads(path.read_text(encoding='utf-8'))
    declared = {
        str(item.get('path')) for item in payload.get('files', [])
        if isinstance(item, dict) and item.get('path')
    }
    actual: set[str] = set()
    for file in base.rglob('*'):
        if not file.is_file():
            continue
        rel = file.relative_to(base)
        if any(part in IGNORED_PARTS for part in rel.parts):
            continue
        if rel.as_posix() == 'MANIFEST.json':
            continue
        actual.add(rel.as_posix())

    unlisted = sorted(actual - declared)
    missing = sorted(declared - actual)
    return {
        'present': True,
        'generated': payload.get('generated'),
        'declared_files': len(declared),
        'actual_files': len(actual),
        'unlisted_files': unlisted,
        'missing_declared_files': missing,
        'is_current_inventory': not unlisted and not missing,
    }


def repository_truth_status(root: Path | None = None) -> dict:
    base = _root(root)
    return {
        'modules': module_status_truth(base),
        'manifest': manifest_truth(base),
        'truth_rule': (
            'Current main plus module contracts, source/provenance records, publication gates '
            'and CI are authoritative. MANIFEST.json is authoritative only when its inventory '
            'matches the current repository tree.'
        ),
    }
