from __future__ import annotations
import io, re, zipfile, yaml

def slugify(text: str) -> str:
    s=re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
    return s or "new_module"

def build_module_zip(name: str, description: str, geography: str="village", temporal: str="cross_sectional") -> tuple[str, bytes]:
    module_id=slugify(name)
    meta={
      "id": module_id,
      "name": name.strip() or module_id.replace("_"," ").title(),
      "version":"0.1.0",
      "status":"active",
      "description": description.strip() or "New JLA module.",
      "geography":{"primary": geography},
      "temporal":{"type": temporal},
      "features":{"map":True,"download":True,"report":True,"comparison":True},
      "dependencies":["core_geography"],
    }
    mem=io.BytesIO()
    with zipfile.ZipFile(mem,"w",zipfile.ZIP_DEFLATED) as z:
        base=f"{module_id}/"
        z.writestr(base+"module.yaml", yaml.safe_dump(meta,sort_keys=False,allow_unicode=True))
        z.writestr(base+"sources.yaml", "sources: []\n")
        z.writestr(base+"schema.yaml", "fields:\n  - name: place_id\n    type: string\n    required: true\n")
        z.writestr(base+"data/indicators.csv", "place_id,indicator_id,period,value_numeric,value_text,unit,source_id,quality_class,observation_type\n")
        z.writestr(base+"README.md", f"# {meta['name']}\n\n{meta['description']}\n\nAdd standardized observations to `data/indicators.csv`. JLA discovers the module automatically.\n")
        z.writestr(base+"tests/test_contract.py", "from pathlib import Path\nimport yaml\n\ndef test_module_contract():\n    p=Path(__file__).resolve().parents[1]/'module.yaml'\n    m=yaml.safe_load(p.read_text())\n    assert {'id','name','version','status','description'} <= set(m)\n")
    return module_id, mem.getvalue()
