from pathlib import Path


def test_modules_page_uses_governed_health_publication_status():
    text = Path("app_pages/modules.py").read_text(encoding="utf-8")
    assert "from jla.health_publication import health_publication_status" in text
    assert "publication = health_publication_status()" in text
    assert "publication['satisfied_count']" in text
    assert "publication[\"publication_allowed\"]" in text
    assert "publication[\"unresolved_gates\"]" in text


def test_modules_page_does_not_equate_health_acquisition_with_completion():
    text = Path("app_pages/modules.py").read_text(encoding="utf-8")
    assert "Acquisition success or green CI cannot promote this module to COMPLETE" in text
    assert "No identifier or geography equivalence is inferred from names alone" in text
