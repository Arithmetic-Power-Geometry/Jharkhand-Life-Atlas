#!/usr/bin/env python3
"""Fail-closed verifier for Module 2 external exact-head CI attestations.

The candidate tree cannot truthfully contain its own Git SHA. Completion therefore
requires a post-commit attestation obtained from GitHub for the immutable candidate.
This verifier validates such an attestation; it never changes scientific gates.
"""
import argparse
import json
import re
from pathlib import Path

REPOSITORY = "Arithmetic-Power-Geometry/Jharkhand-Life-Atlas"
REQUIRED_CHECKS = {"tests", "health-access-validation"}
SHA40 = re.compile(r"^[0-9a-f]{40}$")


def verify_attestation(attestation, candidate_sha):
    errors = []
    if not SHA40.fullmatch(str(candidate_sha or "")):
        errors.append("candidate_sha must be a 40-character lowercase Git SHA")
    if attestation.get("repository") != REPOSITORY:
        errors.append("repository mismatch")
    if attestation.get("candidate_sha") != candidate_sha:
        errors.append("stale or wrong candidate SHA")
    if attestation.get("conclusion") != "success":
        errors.append("CI conclusion is not success")
    run_id = attestation.get("run_id")
    if not isinstance(run_id, int) or isinstance(run_id, bool) or run_id <= 0:
        errors.append("missing or invalid workflow run id")
    run_url = str(attestation.get("run_url") or "")
    expected_prefix = f"https://github.com/{REPOSITORY}/actions/runs/"
    if not run_url.startswith(expected_prefix):
        errors.append("missing or wrong-repository workflow run URL")
    completed_at = str(attestation.get("completed_at") or "").strip()
    if not completed_at:
        errors.append("missing completion timestamp")
    checks = attestation.get("checks")
    if not isinstance(checks, dict):
        errors.append("missing check set")
    else:
        for check in REQUIRED_CHECKS:
            if checks.get(check) != "success":
                errors.append(f"required check not successful: {check}")
    return errors


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("attestation", type=Path)
    parser.add_argument("candidate_sha")
    args = parser.parse_args()
    try:
        payload = json.loads(args.attestation.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"invalid attestation: {exc}")
    errors = verify_attestation(payload, args.candidate_sha)
    if errors:
        raise SystemExit("attestation rejected: " + "; ".join(errors))
    print("health exact-head CI attestation verified")


if __name__ == "__main__":
    main()
