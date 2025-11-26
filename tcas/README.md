TCAS experiment folder

- Prerequisites
- Make sure gcov is installed
- Make sure proofcov exists on path 
For example, add 

#!/bin/bash
python /home/ptr/richtest/proofcov/proofcov/proofcov.py "$@"

to a file /usr/local/bin/proofcov 

- By running python experiment.py 0 1 it will run the coverage comparison between line coverage from gcov and proof-based line coverage from proofcov on the first test case in the test suite. 
