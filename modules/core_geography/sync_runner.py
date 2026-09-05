"""Run the official sync with a narrowly-scoped Census India TLS workaround.

The Census NADA server currently presents a certificate chain that some GitHub-hosted
runners cannot validate. Verification is disabled ONLY for censusindia.gov.in; every
other HTTPS request (including LGD) keeps normal certificate verification. Downloaded
files are still hashed, structurally validated, filtered to Jharkhand, and subjected to
hard count checks before publication.
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

from sync_official import main  # noqa: E402

if __name__ == "__main__":
    main()
