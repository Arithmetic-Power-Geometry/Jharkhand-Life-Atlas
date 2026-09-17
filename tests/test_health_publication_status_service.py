from jla.health_publication import health_publication_ledger, health_publication_status


def test_health_publication_status_is_derived_from_governed_ledger():
    ledger = health_publication_ledger()
    status = health_publication_status()
    gates = ledger["gates"]

    assert status["gate_count"] == len(gates)
    assert status["satisfied_count"] + status["unresolved_count"] == len(gates)
    assert set(status["satisfied_gates"]) == {
        name for name, gate in gates.items() if gate["satisfied"] is True
    }
    assert set(status["unresolved_gates"]) == {
        name for name, gate in gates.items() if gate["satisfied"] is not True
    }


def test_health_publication_status_fails_closed_while_any_gate_is_unresolved():
    status = health_publication_status()
    if status["unresolved_count"]:
        assert status["publication_allowed"] is False
        assert status["module_complete"] is False
        assert status["status"] != "COMPLETE"


def test_health_publication_status_exposes_reasons_for_unresolved_gates():
    status = health_publication_status()
    for name in status["unresolved_gates"]:
        assert str(status["gates"][name].get("reason", "")).strip(), name
