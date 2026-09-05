"""Run Module 1's authoritative Census/LGD synchronisation.

Compatibility handling is deliberately narrow and auditable:
1. Census India's NADA TLS chain is not trusted by some GitHub-hosted runners, so
   certificate verification is disabled ONLY for censusindia.gov.in. Other hosts,
   including LGD, retain normal TLS verification.
2. The national Census Location Code Directory contains aggregate rows. Within
   Jharkhand, only official Census-2011 district codes 346–369 are accepted.
3. The national 'basic population' workbook exposed by Census currently yields the
   town slice in practice. For the village baseline, this runner therefore reads all
   24 official Jharkhand PCA-TV district workbooks (PC11_PCA-TV-2001…2024), which are
   explicitly published at district/sub-district/village/town/ward granularity.

No mirror data are used. Every downloaded official workbook is SHA-256 hashed and a
manifest is written with the curated outputs.
"""
from __future__ import annotations

from pathlib import Path
from urllib.parse import urlparse
import warnings
import requests
import pandas as pd
from urllib3.exceptions import InsecureRequestWarning

_original_request = requests.sessions.Session.request


def _request(self, method, url, **kwargs):
    host = (urlparse(str(url)).hostname or "").lower()
    if host in {"censusindia.gov.in", "www.censusindia.gov.in"}:
        kwargs["verify"] = False
    return _original_request(self, method, url, **kwargs)


requests.sessions.Session.request = _request
warnings.filterwarnings("ignore", category=InsecureRequestWarning, module="urllib3")

import sync_official as sync  # noqa: E402

_original_read_excel_smart = sync.read_excel_smart


def _read_excel_smart(path):
    df = _original_read_excel_smart(path)
    if path.name.lower() == "pc11_tv_dir.xlsx":
        cols = list(df.columns)
        state_c = sync.find_col(cols, ["state code", "state/ut code", "state_union_territory_ut_code"], ["state", "code"])
        dist_c = sync.find_col(cols, ["district code"], ["district", "code"])
        if state_c and dist_c:
            state = df[state_c].map(sync.digits).str.zfill(2)
            district = df[dist_c].map(sync.digits)
            valid = district.apply(lambda x: (not x) or (x.isdigit() and 346 <= int(x) <= 369))
            df = df[(state != "20") | valid].copy()
    return df


sync.read_excel_smart = _read_excel_smart


def _pick_col(cols, aliases, contains=None):
    return sync.find_col(list(cols), aliases, contains)


def _value(r, col):
    if not col:
        return ""
    v = r[col]
    return "" if pd.isna(v) else str(v).strip()


def _parse_pca_tv(path: Path) -> pd.DataFrame:
    df = _original_read_excel_smart(path)
    cols = list(df.columns)
    state_c = _pick_col(cols, ["state", "state code"], ["state"])
    dist_c = _pick_col(cols, ["district", "district code"], ["district"])
    sub_c = _pick_col(cols, ["subdistt", "sub-district", "sub district", "subdistrict code"], ["sub"])
    tv_c = _pick_col(cols, ["town/village", "town village", "village code", "location code"], ["town", "village"])
    ward_c = _pick_col(cols, ["ward"], ["ward"])
    level_c = _pick_col(cols, ["level"], ["level"])
    name_c = _pick_col(cols, ["name", "area name"], ["name"])

    if not tv_c or not name_c:
        raise RuntimeError(f"PCA-TV identity columns not recognised in {path.name}: {cols[:30]}")

    metric_aliases = {
        "households": ["no_hh", "number of households"],
        "population_total": ["tot_p", "population total", "total population persons"],
        "population_male": ["tot_m", "population male", "total population males"],
        "population_female": ["tot_f", "population female", "total population females"],
        "age_0_6_total": ["p_06", "population 0-6 years old", "population in age group 0-6 years persons"],
        "sc_total": ["p_sc", "population of scheduled castes total", "scheduled caste population persons"],
        "st_total": ["p_st", "population of scheduled tribes total", "scheduled tribe population persons"],
        "literate_total": ["p_lit", "population literate", "literates persons"],
        "illiterate_total": ["p_illit", "population illiterate", "illiterates persons"],
        "worker_total": ["p_work", "total workers persons"],
        "main_worker_total": ["mainwork_p", "main workers persons"],
        "marginal_worker_total": ["margwork_p", "marginal workers persons"],
        "main_cultivator_total": ["main_cl_p", "main workers cultivators persons"],
        "main_agri_labour_total": ["main_al_p", "main workers agricultural labourers persons"],
        "main_household_industry_total": ["main_hh_p", "main workers workers in household industries persons"],
        "main_other_worker_total": ["main_ot_p", "main workers other workers persons"],
    }
    metric_cols = {}
    for out, aliases in metric_aliases.items():
        found = None
        for alias in aliases:
            found = _pick_col(cols, [alias])
            if found:
                break
        if not found:
            tokens = [x for x in sync.norm(aliases[-1]).split("_") if x not in {"of", "in", "the"}]
            found = _pick_col(cols, [], tokens[:3] if tokens else None)
        metric_cols[out] = found

    rows = []
    for _, r in df.iterrows():
        level = _value(r, level_c).lower()
        ward = sync.digits(_value(r, ward_c)) if ward_c else ""
        code = sync.digits(_value(r, tv_c))
        name = _value(r, name_c)
        # Census uses ward code 0000 for the whole village/town record.
        if level_c:
            if not ("village" in level or "town" in level):
                continue
            if "ward" in level:
                continue
        if ward and int(ward) != 0:
            continue
        if not code or not name:
            continue
        state = sync.digits(_value(r, state_c)) if state_c else "20"
        if state and state.zfill(2) != "20":
            continue
        d = sync.digits(_value(r, dist_c)) if dist_c else ""
        sd = sync.digits(_value(r, sub_c)) if sub_c else ""
        row = {
            "place_code": code.zfill(6),
            "district_code": d.zfill(3) if d else "",
            "subdistrict_code": sd.zfill(5) if sd else "",
            "name": name,
            "reference_year": "2011",
            "source_id": "CENSUS_PCA_TV_JH_2011",
            "observation_type": "observed",
        }
        for out, col in metric_cols.items():
            row[out] = _value(r, col)
        rows.append(row)
    return pd.DataFrame(rows)


def _build_village_population_from_24(_unused_national_path):
    frames = []
    manifest = []
    for seq in range(1, 25):
        ref = f"20{seq:02d}"
        catalog_id = 6536 + seq
        filename = f"DDW_PCA{ref}_2011_MDDS with UI.xlsx"
        catalog = f"https://censusindia.gov.in/nada/index.php/catalog/{catalog_id}"
        url = sync.discover_download(catalog, filename=filename)
        data = sync.get(url, binary=True)
        if not isinstance(data, bytes) or len(data) < 10_000:
            raise RuntimeError(f"Implausible PCA-TV download for {ref}: {url}")
        path = sync.RAW / filename
        path.write_bytes(data)
        part = _parse_pca_tv(path)
        if part.empty:
            raise RuntimeError(f"No village/town rows parsed from official PCA-TV {ref}")
        frames.append(part)
        manifest.append({
            "reference_id": f"PC11_PCA-TV-{ref}",
            "catalog_id": catalog_id,
            "filename": filename,
            "url": url,
            "sha256": sync.sha256_bytes(data),
            "bytes": len(data),
            "rows_parsed": len(part),
        })

    out = pd.concat(frames, ignore_index=True)
    out = out.drop_duplicates(subset=["place_code", "name"], keep="first")
    if len(out) < 30_000:
        raise RuntimeError(f"Expected >30,000 Jharkhand PCA-TV place rows, got {len(out)}")
    populated = sum(1 for c in ["households", "population_total", "population_male", "population_female",
                                "age_0_6_total", "sc_total", "st_total", "literate_total", "worker_total"]
                    if c in out.columns and (out[c].astype(str).str.strip() != "").any())
    if populated < 8:
        raise RuntimeError(f"PCA-TV demographic parsing too sparse: only {populated} core fields populated")
    pd.DataFrame(manifest).to_csv(sync.OUT / "pca_source_manifest_2011.csv", index=False)
    return out, {"rows": int(len(out)), "district_workbooks": 24, "core_fields_populated": int(populated)}


sync.build_basic_population = _build_village_population_from_24

if __name__ == "__main__":
    sync.main()
