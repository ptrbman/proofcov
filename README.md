# ProofSlice

A (very) simple prototype for proof-based slicing. To use, the following prerequisites are necessary (listed version has been tested):
- Python 3.10.12
- z3 4.8.12 (SMT solver)

## Installation Instructions

Ensure prerequisites. Python is usually installed and install z3, e.g., via apt:
```console
sudo apt install z3
```

Please clone repository:
```console
git clone https://github.com/ptrbman/proofslice.git
```

Create virtual environment and activate:
```console
python -m venv pyenv
source pyenv/bin/activate
```

Install required Python packages:
```console
pip install rich
pip install pycparser
```

## Running ProofSlice
The following command runs the ```addmul`` example:
```console
python proofslice/proofslice.py examples/addmul.c
```
which should yield the following output:
```console
Opening file examples/addmul.c
╭─── C code after unrolling loops ───╮
│ void main() {                      │
│     int sum = 0;                   │
│     int prod = 1;                  │
│                                    │
│     for (int i = 1; i <= 5; i++) { │
│         sum = sum + i;             │
│         prod = prod * i;           │
│     }                              │
│                                    │
│     assert(sum == 15);             │
│ }                                  │
╰────────────────────────────────────╯
╭────────────╮
│ Goto code: │
╰────────────╯
FUN main():
        DECL(sum.0, 0)
        DECL(prod.0, 1)
        sum.1 := sum.0 + 1
        prod.1 := prod.0 * 1
        sum.2 := sum.1 + 2
        prod.2 := prod.1 * 2
        sum.3 := sum.2 + 3
        prod.3 := prod.2 * 3
        sum.4 := sum.3 + 4
        prod.4 := prod.3 * 4
        sum.5 := sum.4 + 5
        prod.5 := prod.4 * 5
        ASSERT(sum.5 == 15)
╭──────────────╮
│ SMT formula: │
╰──────────────╯
(declare-fun sum.0 () (Int))
(declare-fun sum.1 () (Int))
(declare-fun sum.2 () (Int))
(declare-fun sum.3 () (Int))
(declare-fun sum.4 () (Int))
(declare-fun sum.5 () (Int))
(declare-fun prod.0 () (Int))
(declare-fun prod.1 () (Int))
(declare-fun prod.2 () (Int))
(declare-fun prod.3 () (Int))
(declare-fun prod.4 () (Int))
(declare-fun prod.5 () (Int))
(assert (! (= sum.0 0) :named line2.0)) ; line 2
(assert (! (= prod.0 1) :named line3.0)) ; line 3
(assert (! (= sum.1 (+ sum.0 1)) :named line5.0)) ; line 5
(assert (! (= prod.1 (* prod.0 1)) :named line6.0)) ; line 6
(assert (! (= sum.2 (+ sum.1 2)) :named line7.0)) ; line 7
(assert (! (= prod.2 (* prod.1 2)) :named line8.0)) ; line 8
(assert (! (= sum.3 (+ sum.2 3)) :named line9.0)) ; line 9
(assert (! (= prod.3 (* prod.2 3)) :named line10.0)) ; line 10
(assert (! (= sum.4 (+ sum.3 4)) :named line11.0)) ; line 11
(assert (! (= prod.4 (* prod.3 4)) :named line12.0)) ; line 12
(assert (! (= sum.5 (+ sum.4 5)) :named line13.0)) ; line 13
(assert (! (= prod.5 (* prod.4 5)) :named line14.0)) ; line 14
(assert (! (not (= sum.5 15)) :named line16.0)) ; line 16
(check-sat)

╭─────────────╮
│ Unsat core: │
╰─────────────╯
{2, 5, 7, 9, 11, 13, 16}
╭───────────────╮
│ Marked lines: │
╰───────────────╯
{2, 10, 6}
╭────── C code with marked lines ───────╮
│ 1: void main() {                      │
│ 2:     int sum = 0;                   │
│ 3:     int prod = 1;                  │
│ 4:                                    │
│ 5:     for (int i = 1; i <= 5; i++) { │
│ 6:         sum = sum + i;             │
│ 7: //         prod = prod * i;        │
│ 8:     }                              │
│ 9:                                    │
│ 10:     assert(sum == 15);            │
│ 11: }                                 │
╰───────────────────────────────────────╯
```

## Validation
Whenever ProofSlice is executed, it stores the sliced C code into ```tmp.c```. To validate the slice, please compile and execute the slice, for example with ```gcc```:
```console
gcc tmp.c && ./a.out
```

## Bugs
Please report any bugs or contact me if you have any questions!



