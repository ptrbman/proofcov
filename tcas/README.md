# TCAS experiment folder
Due to license restrictions I can not provide you with the tcas source file. Please contact me and I can assist you in how to obtain it.

## Prerequisites
- Make sure gcov is installed
- Make sure proofcov exists on path 
For example, add 

```bash
#!/bin/bash
python /home/ptr/richtest/proofcov/proofcov/proofcov.py "$@"
```
to a file ```/usr/local/bin/proofcov```

- By running python experiment.py 0 1 it will run the coverage comparison between line coverage from gcov and proof-based line coverage from proofcov on the first test case in the test suite. 
