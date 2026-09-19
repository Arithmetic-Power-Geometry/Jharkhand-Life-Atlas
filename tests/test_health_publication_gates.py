import json
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
LEDGER = ROOT / "modules" / "health_access" / "publication_gates.json"
REQUIRED_GATES = {
    "validated_historical_census2011_layer",
    "priority_current_payloads_authoritatively_acquired",
    "immutable_raw_or_api_provenance_complete",
    "rights_and_attribution_complete",
    "observed_schema_and_semantics_validated",
    "record_level_temporal_interpretation_validated",
    "geographic_linkage_evidence_backed",
    "privacy_safe_curated_current_tables",
    "derived_indicators_supported",
    "research_ready_downloads_reports_current_layer",
    "streamlit_synchronized_with_validated_outputs",
    "exact_final_main_green_ci",
}


def _ledger():
    return json.loads(LEDGER.read_text(encoding="utf-8"))


def _repository_evidence_path(relative_path, gate_name):
    assert isinstance(relative_path, str) and relative_path.strip(), gate_name
    assert relative_path == relative_path.strip(), (
        f"{gate_name}: evidence path has surrounding whitespace"
    )
    candidate = Path(relative_path)
    assert not candidate.is_absolute(), (
        f"{gate_name}: evidence path must be repository-relative: {relative_path}"
    )
    unresolved = ROOT / candidate
    # Reject symlinks anywhere in the evidence path, not only at the leaf.
    current = ROOT
    for part in candidate.parts:
        current = current / part
        assert not current.is_symlink(), (
            f"{gate_name}: publication evidence path contains a symlink: {relative_path}"
        )
    resolved = unresolved.resolve()
    try:
        resolved.relative_to(ROOT.resolve())
    except ValueError as exc:
        raise AssertionError(
            f"{gate_name}: evidence path escapes repository: {relative_path}"
        ) from exc
    return resolved


def _tracked_blob(relative_path, gate_name):
    result = subprocess.run(
        ["git", "ls-files", "-s", "--", relative_path],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0 and result.stdout.strip(), (
        f"{gate_name}: publication evidence is not version-controlled: {relative_path}"
    )
    rows = [line for line in result.stdout.splitlines() if line.strip()]
    assert len(rows) == 1, f"{gate_name}: ambiguous Git index entry: {relative_path}"
    fields = rows[0].split(None, 3)
    assert len(fields) == 4 and fields[2] == "0", (
        f"{gate_name}: unexpected Git index entry: {relative_path}"
    )
    return fields[1]


def _working_tree_blob(relative_path, gate_name):
    result = subprocess.run(
        ["git", "hash-object", "--", relative_path],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    blob = result.stdout.strip()
    assert result.returncode == 0 and blob, (
        f"{gate_name}: cannot hash publication evidence bytes: {relative_path}"
    )
    return blob


def test_health_publication_gate_ledger_is_fail_closed():
    ledger = _ledger()
    assert ledger["module"] == "health_access"
    assert ledger["status"] in {"COMPLETE", "IN DEVELOPMENT", "PLANNED"}
    assert isinstance(ledger["publication_allowed"], bool)
    assert isinstance(ledger["module_complete"], bool)
    assert ledger["gates"]
    assert set(ledger["gates"]) == REQUIRED_GATES, (
        "health publication gate inventory changed; required scientific/publication "
        "gates must not be deleted, renamed, or silently bypassed"
    )

    for name, gate in ledger["gates"].items():
        assert isinstance(gate.get("satisfied"), bool), name
        if not gate["satisfied"]:
            assert str(gate.get("reason", "")).strip(), name

    all_satisfied = all(gate["satisfied"] for gate in ledger["gates"].values())
    if ledger["module_complete"] or ledger["publication_allowed"]:
        assert all_satisfied
        assert ledger["module_complete"] is True
        assert ledger["publication_allowed"] is True
        assert ledger["status"] == "COMPLETE"
    else:
        assert ledger["status"] != "COMPLETE"


def test_satisfied_health_gates_reference_repository_evidence():
    ledger = _ledger()
    for name, gate in ledger["gates"].items():
        if not gate["satisfied"]:
            continue
        evidence = gate.get("evidence")
        blob_bindings = gate.get("evidence_git_blobs")
        assert isinstance(evidence, list) and evidence, name
        assert len(evidence) == len(set(evidence)), f"{name}: duplicate evidence paths"
        assert isinstance(blob_bindings, dict), f"{name}: missing immutable Git blob bindings"
        assert set(blob_bindings) == set(evidence), (
            f"{name}: every evidence path must have exactly one immutable Git blob binding"
        )
        for relative_path in evidence:
            path = _repository_evidence_path(relative_path, name)
            assert path.exists(), f"{name}: missing evidence {relative_path}"
            assert path.is_file(), f"{name}: evidence is not a file {relative_path}"
            assert path.stat().st_size > 0, (
                f"{name}: publication evidence is empty {relative_path}"
            )
            expected_blob = blob_bindings[relative_path]
            assert isinstance(expected_blob, str) and len(expected_blob) == 40, (
                f"{name}: invalid Git blob binding for {relative_path}"
            )
            actual_blob = _tracked_blob(relative_path, name)
            assert actual_blob == expected_blob, (
                f"{name}: publication evidence bytes changed without gate re-review: {relative_path}"
            )
            working_blob = _working_tree_blob(relative_path, name)
            assert working_blob == expected_blob, (
                f"{name}: working-tree publication evidence differs from reviewed bytes: {relative_path}"
            )


def test_current_health_ledger_does_not_overclaim_completion():
    ledger = _ledger()
    unsatisfied = {
        name for name, gate in ledger["gates"].items() if not gate["satisfied"]
    }
    if unsatisfied:
        assert ledger["module_complete"] is False
        assert ledger["publication_allowed"] is False
        assert ledger["status"] == "IN DEVELOPMENT"
