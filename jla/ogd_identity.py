"""Fail-closed identity classification for observed Government Open Data URLs.

This module does not perform acquisition and never synthesizes resource identifiers.
It only classifies identifiers that are explicitly present in an observed official URL.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urlparse

_UUID = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-"
    r"[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$"
)
_ALLOWED_HOSTS = {"data.gov.in", "www.data.gov.in", "api.data.gov.in"}


@dataclass(frozen=True)
class OGDIdentity:
    url: str
    official_host: bool
    identity_kind: str
    explicit_id: str | None
    machine_payload_endpoint: bool


def classify_ogd_url(url: str) -> OGDIdentity:
    """Classify one observed OGD URL without inferring missing identity.

    ``/apis/<uuid>`` is catalog/API-description identity only. It must never be
    promoted to a downloadable resource identifier. A machine-resource candidate
    is recognized only when the observed host is ``api.data.gov.in`` and the
    observed path itself contains ``/resource/<uuid>``.
    """
    try:
        parsed = urlparse(url)
    except (TypeError, ValueError):
        return OGDIdentity(str(url), False, "invalid", None, False)

    host = (parsed.hostname or "").lower()
    if parsed.scheme not in {"http", "https"} or host not in _ALLOWED_HOSTS:
        return OGDIdentity(str(url), False, "untrusted_or_invalid", None, False)

    parts = [part for part in parsed.path.split("/") if part]
    if len(parts) >= 2 and parts[0] == "apis" and _UUID.fullmatch(parts[1]):
        return OGDIdentity(str(url), True, "catalog_api", parts[1].lower(), False)

    if len(parts) >= 2 and parts[0] == "resource":
        explicit = parts[1].lower() if _UUID.fullmatch(parts[1]) else None
        if host == "api.data.gov.in" and explicit:
            return OGDIdentity(str(url), True, "machine_resource_candidate", explicit, True)
        return OGDIdentity(str(url), True, "resource_page", explicit, False)

    return OGDIdentity(str(url), True, "official_page", None, False)


def explicit_machine_resource_id(url: str) -> str | None:
    """Return only an explicitly observed machine-resource UUID, otherwise null."""
    identity = classify_ogd_url(url)
    if not identity.machine_payload_endpoint:
        return None
    return identity.explicit_id
