from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REVIEW = ROOT / "modules" / "health_access" / "RIGHTS_LICENCE_REVIEW.md"
EXPECTED_NHD_SHA256 = "1ddcad9f9b922142a4374c7b89b70fb6cefd8a257448c70a61e1c07d98845134"


def _text():
    return REVIEW.read_text(encoding="utf-8")


def test_rights_review_acknowledges_verified_primary_nhd_payload_binding():
    text = _text()

    assert "10,341,256 bytes" in text
    assert EXPECTED_NHD_SHA256 in text
    assert "one explicit primary official `data.gov.in` payload" in text
    assert "nhd_primary_payload_binding_2026-09-14.json" in text


def test_rights_review_keeps_nhd_publication_fail_closed_after_acquisition():
    text = _text().lower()

    assert "publication remains prohibited" in text
    assert "alternate official alias remains unresolved" in text
    assert "row-level temporal semantics" in text
    assert "administrative-vintage/geographic linkage" in text
    assert "systematic-zero field semantics" in text
    assert "privacy-safe row curation" in text
    assert "indicator validity" in text


def test_rights_review_does_not_allow_hash_match_to_bypass_scientific_gates():
    text = _text().lower()

    assert "successful acquisition or a byte-level hash match is also insufficient by itself" in text
    assert "scientific semantics" in text
    assert "temporal support" in text
    assert "geographic support" in text
    assert "privacy-safe curation" in text
    assert "validation remain independent mandatory gates" in text


def test_rights_review_preserves_privacy_and_missingness_boundaries():
    text = _text().lower()

    assert "person-level, patient-level or otherwise sensitive health records" in text
    assert "prohibited" in text
    assert "missing source values remain null/blank representations" in text
    assert "census-2011 to current-lgd equivalence based on names" in text
