# ProofCov

A (very) simple prototype for proof-based slicing. It only works for a narrow subset of C mostly works for the cases in the ```examples``` folder. To use, the following prerequisites are necessary (listed version has been tested):
- Python 3.13.7
- Python packages (installed below): z3-solver 5.1.0, pycparser 3.0, rich 15.0.0, graphviz 0.21
- Graphviz (only needed for `--graph`)

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
If the assertion can fail, ProofCov prints `Test fail` and exits with code 1.

Options:
- `--line`: report line coverage
- `--branch`: report branch coverage
- `--all`: report both line and branch coverage
- `--enumerate-cores`: find all minimal proofs (unsat cores) and report coverage for each of them, instead of a single one
- `-v`, `--verbose`: show the program, GOTO code, SMT formula, unsat core and covered lines in detail
- `--graph`: draw the control flow graph, colored by line coverage, as PNG files in `tmp/`
- `--experiment`: only print the covered lines (`COVERED: ...`), used by the TCAS experiment
- `--track-undef`: use an alternative encoding which tracks undefined values

## Running the tests
```console
python tests/run_tests.py
```

## Bugs
Please report any bugs or contact me if you have any questions!
