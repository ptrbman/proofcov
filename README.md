# ProofCov

A (very) simple prototype for proof-based slicing. It only works for a narrow subset of C mostly works for the cases in the ```examples``` folder. To use, the following prerequisites are necessary (listed version has been tested):
- Python 3.13.7
- Python packages (installed below): z3-solver 5.1.0, pycparser 3.0, rich 15.0.0, graphviz 0.21
- Graphviz (only needed for `--graph`)
- gcc (only needed for programs with `#define`)

For a step-by-step introduction with examples and an explanation of the output, see the [tutorial](docs/TUTORIAL.md).

## Installation Instructions

Ensure prerequisites. Python is usually installed. Graphviz is only needed to draw control flow graphs (`--graph`) and can be installed, e.g., via apt:
```console
sudo apt install graphviz
```

Please clone repository:
```console
git clone https://github.com/ptrbman/proofcov.git
```

Create virtual environment and activate:
```console
python -m venv pyenv
source pyenv/bin/activate
```

Install required Python packages:
```console
pip install z3-solver
pip install rich
pip install pycparser
pip install graphviz
```

## Running ProofCov
ProofCov takes a C program consisting of a single `main` function ending with an `assert`. It proves the assertion with z3 and reports which lines were needed for the proof (the unsat core):
```console
python proofcov/proofcov.py examples/dilemma.c --all
```
```
[proofcov] Opening file examples/dilemma.c
Line coverage: 6/8 (75.00%)
Branch coverage: 2/4 (50.00%)
```
If the assertion can fail, ProofCov prints `Test fail` and exits with code 1. If the program can not be analyzed (it is not valid C or uses an unsupported construct), ProofCov prints an error message and exits with code 2.

Options:
- `--line`: report line coverage
- `--branch`: report branch coverage
- `--all`: report both line and branch coverage
- `--enumerate-cores`: find all minimal proofs (unsat cores) and report coverage for each of them, instead of a single one
- `-v`, `--verbose`: show the program, GOTO code, SMT formula, unsat core and covered lines in detail
- `--graph`: draw the control flow graph, colored by line coverage, as PNG files in `tmp/`
- `--experiment`: print machine-readable output (`COVERED: ...` and more, see the tutorial), used by the TCAS experiment
- `--track-undef`: use an alternative encoding which tracks undefined values

ProofCov rewrites the program into the supported subset of C before the analysis (`proofcov/normalize.py`): `#define`, global variables, arrays of constant size, functions without parameters (inlined), `?:` and truth values assigned to integers (`x = a && b;` becomes an if-statement) are supported. Loops, pointers and functions with parameters are not.

## The tcas experiment
`tcas` contains the scripts of the tcas experiment of the paper, which compares proofcov with gcov, see `tcas/README.md`. The tcas source is licensed and not part of the repository.

## Running the tests
```console
python tests/run_tests.py
```

## Bugs
Please report any bugs or contact me if you have any questions!
