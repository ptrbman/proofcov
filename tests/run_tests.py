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
import re
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
    "initialized_decls.c": [{2, 4, 5, 7}],
    # Several statements on one line: the line is covered if any of them is in the core
    "same_line_assignments.c": [{4, 5}],
    "same_line_declarations.c": [{2, 3}],
    "same_line_if.c": [{4, 6, 7}],
    "no_branches.c": [{4, 5, 6}],
    # Empty blocks {} in an if
    "empty_else.c": [{4, 6, 7, 10}],
    "empty_then.c": [{4, 6, 8, 10}],
    # Numbers used as truth values (if (a), !a, a && b, assert(x)) mean != 0, as in C
    "int_condition.c": [{4, 6, 7, 9}],
    "int_logic.c": [{5, 6, 8, 9, 11}],
    "int_assert.c": [{3, 4}],
    # Front-end rewriting (normalize.py): truth value assigned to an int, functions, globals,
    # arrays, ?:, #define and a multi-line comment (line numbers must stay the same)
    "bool_assignment.c": [{4, 5, 6}],
    "functions.c": [{5, 6, 10, 15, 16, 17, 20}],
    "arrays_ternary.c": [{11, 13, 14, 15, 16}],
    # / and % round towards zero as in C (SMT-LIB div/mod would give -4 and 1)
    "c_division.c": [{6, 7, 8, 9, 10}],
    # Global variables are 0 as in C; the initialization is not a line of the program
    "global_zero_init.c": [{6, 7}],
    # Two ifs on one line
    "two_ifs_one_line.c": [{2, 6, 7}],
    # Division by zero is an error in C, so the program fails (unless the division is not executed)
    "division_by_zero.c": None,
    "guarded_division.c": [{4, 5, 6, 9}],
    # The right side of && is only evaluated if the left side is true, so the body of check()
    # (lines 4-6) is not executed and not covered
    "short_circuit.c": [{11, 12, 13, 16}],
    # Reading a variable before it is assigned is an error, also if its value does not matter
    # or it is only unassigned on the executed path (x == 1 is evaluated before c == 0)
    "uninitialized.c": None,
    "uninitialized_unused_value.c": None,
    "uninitialized_on_path.c": None,
    # x is assigned on the executed path, which the proof must show (line 4)
    "assigned_on_path.c": [{4, 5, 6, 8}],
}

# Expected minimal unsat cores with --track-undef (enumerated, so all of them must be found)
TRACK_UNDEF = {
    "undef_both_branches.c": [{5, 6, 7, 8, 12}],
    "undef_chain.c": [{3, 4, 5, 6, 7, 11}],
    "short_circuit.c": [{11, 12, 13, 16}],
}

# Expected outcomes ("line:true/false") of the statements generated from truth values and ?:,
# for programs with a single minimal core
OUTCOMES = {
    "bool_assignment.c": {"5:true"},
    "functions.c": {"10:false"},
    "arrays_ternary.c": {"15:false"},
}

# Programs proofcov should reject, with (part of) the expected error message
UNSUPPORTED = {
    "condition_as_number.c": "Unsupported: condition used as a number at line 5",
    "unsupported_operator.c": "Unsupported operator << at line 3",
    # The missing semicolon on line 2 is found at the next token
    "parse_error.c": "Parse error at line 3, column 5",
    # A program ends with a single assert
    "two_asserts.c": "the program must end with a single assert",
    "assert_in_branch.c": "the program must end with a single assert",
}

# Expected coverage ("covered/total") reported by --line and --branch.
# Only for programs with a single minimal core, so the result does not depend on the core z3 picks.
LINE_COVERAGE = {
    "initialized_decls.c": "4/5",
    # Several statements on one line count as one line
    "same_line_assignments.c": "2/2",
    "same_line_declarations.c": "2/2",
    "same_line_if.c": "3/4",
    "no_branches.c": "3/3",
    "empty_else.c": "4/5",
    "empty_then.c": "4/5",
    "int_condition.c": "4/5",
    "functions.c": "7/8",
    "arrays_ternary.c": "5/7",
    "global_zero_init.c": "2/2",
    "two_ifs_one_line.c": "3/6",
}

BRANCH_COVERAGE = {
    "initialized_decls.c": "1/1",
    # No if statements: reported as 0/0 instead of dividing by zero
    "no_branches.c": "0/0",
    # An empty branch is not counted, like a missing else
    "empty_else.c": "1/1",
    "empty_then.c": "1/1",
    "int_condition.c": "1/1",
    # The ifs generated from truth values, ?: and array reads (normalize.py) are not branches
    "bool_assignment.c": "0/0",
    "arrays_ternary.c": "0/0",
    "functions.c": "0/1",
    # Two ifs on one line can not be told apart and count as one branch (with a warning)
    "two_ifs_one_line.c": "1/1",
}

# Programs for which --branch should print a warning, with (part of) the expected message
WARNINGS = {
    "two_ifs_one_line.c": "Warning: line 6 has more than one if-statement",
}


# With --track-undef every proof should lie on one execution trace (Theorem 3 of the paper), so lines
# on different sides of an if can not all be in one core. Each program lists such lines.
SAME_TRACE = {
    # b = a only makes b defined if a is, so b == 1 can not be undefined while b has a value
    "undef_both_branches.c": {8, 10},
    "undef_chain.c": {7, 9},
}

# Known failures, reported as XFAIL and not counted as failed
KNOWN_FAILURES = set()


def run_proofcov(program, extra_args, experiment=True):
    path = os.path.join(TESTS_DIR, "programs", program)
    # FORCE_COLOR makes rich print color codes even into a pipe, which breaks parsing
    env = dict(os.environ)
    env.pop("FORCE_COLOR", None)
    result = subprocess.run(
        [sys.executable, PROOFCOV, path] + (["--experiment"] if experiment else []) + extra_args,
        capture_output=True,
        text=True,
        env=env,
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


# kind is "Line" or "Branch"
def check_coverage(program, kind, expected):
    result, _ = run_proofcov(program, ["--" + kind.lower()], experiment=False)
    m = re.search(kind + r" coverage: (\d+/\d+)", result.stdout)
    got = m.group(1) if m else None
    ok = result.returncode == 0 and got == expected

    if ok:
        print(f"PASS  {program} ({kind.lower()} coverage)")
    else:
        print(f"FAIL  {program} ({kind.lower()} coverage): expected {expected}")
        print(f"      got {got}, exit code {result.returncode}")
        if result.stderr:
            print("      stderr:")
            print("\n".join("        " + l for l in result.stderr.splitlines()))
    return ok


def check_outcomes(program, expected):
    result, _ = run_proofcov(program, [])
    got = None
    for line in result.stdout.splitlines():
        if line.startswith("OUTCOMES:"):
            got = set(line.split()[1:])
    ok = result.returncode == 0 and got == expected

    if ok:
        print(f"PASS  {program} (outcomes)")
    else:
        print(f"FAIL  {program} (outcomes): expected {sorted(expected)}")
        print(f"      got {sorted(got) if got is not None else None}, exit code {result.returncode}")
    return ok


def check_warning(program, message):
    result, _ = run_proofcov(program, ["--branch"], experiment=False)
    ok = result.returncode == 0 and message in result.stderr

    if ok:
        print(f"PASS  {program} (warning)")
    else:
        print(f"FAIL  {program} (warning): expected a warning containing '{message}'")
        print(f"      got exit code {result.returncode}, stderr: {result.stderr.strip()!r}")
    return ok


def check_same_trace(program, lines):
    result, cores = run_proofcov(program, ["--track-undef", "--enumerate-cores"])
    bad = [sorted(c) for c in cores if lines <= c]
    ok = result.returncode == 0 and cores and not bad
    known = program in KNOWN_FAILURES

    if ok and known:
        print(f"XPASS {program} (same trace): passes now, remove it from KNOWN_FAILURES")
    elif ok:
        print(f"PASS  {program} (same trace)")
    else:
        print(f"{'XFAIL' if known else 'FAIL '} {program} (same trace): expected no core with all of lines {sorted(lines)}")
        print(f"      got cores {[sorted(c) for c in cores]}, exit code {result.returncode}")
    # Returns "pass", "fail" or "xfail". A known failure that passes is a failure, so that
    # KNOWN_FAILURES is kept up to date.
    if known:
        return "fail" if ok else "xfail"
    return "pass" if ok else "fail"


def check_unsupported(program, message):
    result, _ = run_proofcov(program, [])
    # Exit code 2 and a message, not a traceback (exit code 1 means the assertion can fail)
    ok = result.returncode == 2 and message in result.stderr and "Traceback" not in result.stderr

    if ok:
        print(f"PASS  {program} (unsupported)")
    else:
        print(f"FAIL  {program} (unsupported): expected an error containing '{message}'")
        print(f"      got exit code {result.returncode}")
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
    for program, expected in TRACK_UNDEF.items():
        if not check(program, expected, ["--track-undef", "--enumerate-cores"]):
            failures += 1
    for program, expected in LINE_COVERAGE.items():
        if not check_coverage(program, "Line", expected):
            failures += 1
    for program, expected in BRANCH_COVERAGE.items():
        if not check_coverage(program, "Branch", expected):
            failures += 1
    for program, expected in OUTCOMES.items():
        if not check_outcomes(program, expected):
            failures += 1
    for program, message in WARNINGS.items():
        if not check_warning(program, message):
            failures += 1
    for program, message in UNSUPPORTED.items():
        if not check_unsupported(program, message):
            failures += 1
    xfails = 0
    for program, lines in SAME_TRACE.items():
        status = check_same_trace(program, lines)
        failures += status == "fail"
        xfails += status == "xfail"

    total = (2 * len(EXPECTED) + len(TRACK_UNDEF) + len(LINE_COVERAGE) + len(BRANCH_COVERAGE) + len(OUTCOMES)
             + len(WARNINGS) + len(UNSUPPORTED) + len(SAME_TRACE))
    print(f"\n{total - failures - xfails}/{total - xfails} tests passed" + (f", {xfails} known failure (XFAIL)" if xfails else ""))
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
