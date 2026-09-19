from jla.health_publication import verify_external_ci_attestation

SHA = "a" * 40
REPO = "Arithmetic-Power-Geometry/Jharkhand-Life-Atlas"


def attestation(sha=SHA):
    return {
        "repository": REPO,
        "head_sha": sha,
        "workflow_runs": [
            {"name": "tests", "head_sha": sha, "conclusion": "success", "url": f"https://github.com/{REPO}/actions/runs/1"},
            {"name": "health-access-validation", "head_sha": sha, "conclusion": "success", "url": f"https://github.com/{REPO}/actions/runs/2"},
        ],
    }


def test_exact_head_attestation_requires_both_required_green_workflows():
    assert verify_external_ci_attestation(attestation(), SHA)
    evidence = attestation()
    evidence["workflow_runs"] = evidence["workflow_runs"][:1]
    assert not verify_external_ci_attestation(evidence, SHA)


def test_attestation_fails_closed_for_stale_sha_wrong_repo_or_bad_url():
    assert not verify_external_ci_attestation(attestation("b" * 40), SHA)
    evidence = attestation()
    evidence["repository"] = "other/repo"
    assert not verify_external_ci_attestation(evidence, SHA)
    evidence = attestation()
    evidence["workflow_runs"][0]["url"] = "https://example.com/actions/runs/1"
    assert not verify_external_ci_attestation(evidence, SHA)


def test_attestation_rejects_non_green_and_invalid_candidate_sha():
    evidence = attestation()
    evidence["workflow_runs"][1]["conclusion"] = "failure"
    assert not verify_external_ci_attestation(evidence, SHA)
    assert not verify_external_ci_attestation(attestation(), "not-a-sha")
