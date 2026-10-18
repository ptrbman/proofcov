# TCAS experiment folder
The scripts in this folder compare line coverage from gcov with proof-based line coverage from proofcov on TCAS. The TCAS source is licensed and is not part of this repository, so you have to obtain it yourself to run the experiment.

## Prerequisites
- gcc and gcov
- The TCAS program prepared for proofcov as `proofcov_template.c` in this folder (it is ignored by git)
- The test cases in `solutions.txt` in this folder, one per line: the 12 inputs followed by the expected output, separated by single spaces as in `params.txt`

## Running
Run the scripts from this folder:
```console
cd tcas
mkdir -p tmp
python experiment.py 0 1
```
`experiment.py <start> <end>` runs the coverage comparison between gcov and proofcov on test cases `start` to `end - 1` (counted from 0), so `0 1` runs the first test case.
