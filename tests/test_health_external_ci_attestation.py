from jla.health_publication import verify_external_ci_attestation

SHA = "a" * 40
REPO = "Arithmetic-Power-Geometry/Jharkhand-Life-Atlas"


def attestation(sha=SHA):
    def run(name, run_id):
        return {
            "name": name,
            "head_sha": sha,
            "head_branch": "main",
            "event": "push",
            "conclusion": "success",
            "url": f"https://github.com/{REPO}/actions/runs/{run_id}",
        }
    return {
        "repository": REPO,
        "head_sha": sha,
        "workflow_runs": [run("tests", 1), run("health-access-validation", 2)],
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


def test_attestation_rejects_non_green_invalid_sha_and_non_main_runs():
    evidence = attestation()
    evidence["workflow_runs"][1]["conclusion"] = "failure"
    assert not verify_external_ci_attestation(evidence, SHA)
    assert not verify_external_ci_attestation(attestation(), "not-a-sha")

    evidence = attestation()
    evidence["workflow_runs"][0]["head_branch"] = "feature"
    assert not verify_external_ci_attestation(evidence, SHA)
    evidence = attestation()
    evidence["workflow_runs"][1]["event"] = "pull_request"
    assert not verify_external_ci_attestation(evidence, SHA)
