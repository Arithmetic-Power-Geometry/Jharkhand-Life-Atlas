from scripts.verify_health_ci_attestation import REPOSITORY, verify_attestation


SHA = "a" * 40


def valid_attestation():
    return {
        "repository": REPOSITORY,
        "candidate_sha": SHA,
        "run_id": 123456,
        "run_url": f"https://github.com/{REPOSITORY}/actions/runs/123456",
        "conclusion": "success",
        "completed_at": "2026-09-24T10:00:00Z",
        "checks": {"tests": "success", "health-access-validation": "success"},
    }


def test_valid_external_attestation_passes():
    assert verify_attestation(valid_attestation(), SHA) == []


def test_stale_sha_fails_closed():
    attestation = valid_attestation()
    attestation["candidate_sha"] = "b" * 40
    assert "stale or wrong candidate SHA" in verify_attestation(attestation, SHA)


def test_wrong_repository_fails_closed():
    attestation = valid_attestation()
    attestation["repository"] = "example/wrong"
    assert "repository mismatch" in verify_attestation(attestation, SHA)


def test_non_green_conclusion_fails_closed():
    attestation = valid_attestation()
    attestation["conclusion"] = "failure"
    assert "CI conclusion is not success" in verify_attestation(attestation, SHA)


def test_missing_required_check_fails_closed():
    attestation = valid_attestation()
    del attestation["checks"]["health-access-validation"]
    errors = verify_attestation(attestation, SHA)
    assert "required check not successful: health-access-validation" in errors


def test_missing_attestation_fields_fail_closed():
    errors = verify_attestation({}, SHA)
    assert errors
    assert "missing check set" in errors
