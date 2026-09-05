from __future__ import annotations
from pathlib import Path
import yaml
from .paths import MODULES_DIR

REQUIRED_KEYS = {"id", "name", "version", "status", "description"}

def discover_modules(modules_dir: Path | None = None) -> list[dict]:
    root = modules_dir or MODULES_DIR
    found = []
    if not root.exists():
        return found
    for folder in sorted(p for p in root.iterdir() if p.is_dir() and not p.name.startswith("_")):
        meta_path = folder / "module.yaml"
        if not meta_path.exists():
            continue
        try:
            meta = yaml.safe_load(meta_path.read_text(encoding="utf-8")) or {}
            missing = sorted(REQUIRED_KEYS - set(meta))
            meta["_path"] = str(folder)
            meta["_valid"] = not missing
            meta["_errors"] = [f"Missing key: {k}" for k in missing]
            found.append(meta)
        except Exception as exc:
            found.append({"id": folder.name, "name": folder.name, "version": "?", "status": "error", "description": "Invalid module metadata", "_path": str(folder), "_valid": False, "_errors": [str(exc)]})
    return found

def module_by_id(module_id: str) -> dict | None:
    return next((m for m in discover_modules() if m.get("id") == module_id), None)
