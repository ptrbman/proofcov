#!/usr/bin/env python3
# Simple regression tests for proofcov.
# Generated with Claude Code (Claude Opus 5.5).
#
# Runs proofcov in --experiment mode on the programs in tests/programs and
# checks the covered lines against the minimal unsat cores listed below.
#
# Usage (from anywhere, with the proofcov dependencies installed):
#   python tests/run_tests.py

import os
import subprocess
import sys

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
PROOFCOV = os.path.join(TESTS_DIR, "..", "proofcov", "proofcov.py")

# Expected minimal unsat cores (as sets of source lines) for each program.
# None means the assertion can fail, i.e., proofcov should report "Test fail".
EXPECTED = {
    "single_if.c": [{3, 5, 9}, {5, 6, 9}],
    "two_proofs.c": [{5, 7, 8, 13, 14, 19}, {13, 14, 16, 19}],
    "failing_assert.c": None,
}


def run_proofcov(program, extra_args):
    path = os.path.join(TESTS_DIR, "programs", program)
    result = subprocess.run(
        [sys.executable, PROOFCOV, path, "--experiment"] + extra_args,
        capture_output=True,
        text=True,
    )
    cores = []
    for line in result.stdout.splitlines():
        if line.startswith("COVERED:"):
            cores.append(set(map(int, line.split()[1:])))
    return result, cores


def check(program, expected, extra_args):
    result, cores = run_proofcov(program, extra_args)
    mode = " ".join(extra_args) or "default"

    if expected is None:
        ok = result.returncode == 1 and "Test fail" in result.stdout
        why = "expected 'Test fail' with exit code 1"
    elif extra_args:
        # Enumeration must find exactly the expected cores (in any order)
        ok = result.returncode == 0 and sorted(map(sorted, cores)) == sorted(map(sorted, expected))
        why = f"expected cores {[sorted(c) for c in expected]}"
    else:
        # The single core may be any one of the minimal cores
        ok = result.returncode == 0 and len(cores) == 1 and cores[0] in expected
        why = f"expected one of {[sorted(c) for c in expected]}"

    if ok:
        print(f"PASS  {program} ({mode})")
    else:
        print(f"FAIL  {program} ({mode}): {why}")
        print(f"      got cores {[sorted(c) for c in cores]}, exit code {result.returncode}")
        if result.stderr:
            print("      stderr:")
            print("\n".join("        " + l for l in result.stderr.splitlines()))
    return ok


def main():
    failures = 0
    for program, expected in EXPECTED.items():
        for extra_args in ([], ["--enumerate-cores"]):
            if not check(program, expected, extra_args):
                failures += 1

    total = 2 * len(EXPECTED)
    print(f"\n{total - failures}/{total} tests passed")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
