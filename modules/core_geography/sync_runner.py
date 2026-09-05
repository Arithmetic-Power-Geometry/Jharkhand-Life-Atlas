"""Run the official sync with narrowly-scoped source compatibility fixes.

Census India's NADA server currently presents a certificate chain that some GitHub
hosted runners cannot validate. TLS verification is disabled ONLY for
censusindia.gov.in; every other HTTPS request keeps normal verification.

The national Location Code Directory also contains aggregate/non-district rows inside
the Jharkhand slice. Before the canonical parser sees that workbook, this runner keeps
only official Census-2011 Jharkhand district codes 346–369 for rows carrying a district
code. This prevents aggregate rows from being mistaken for a 25th district while
preserving the original downloaded file hash in the sync report.
"""
from __future__ import annotations

from urllib.parse import urlparse
import warnings
import requests
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
            valid_jh_district = district.apply(lambda x: (not x) or (x.isdigit() and 346 <= int(x) <= 369))
            df = df[(state != "20") | valid_jh_district].copy()
    return df


sync.read_excel_smart = _read_excel_smart

if __name__ == "__main__":
    sync.main()
