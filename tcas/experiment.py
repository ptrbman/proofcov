  
from rich import print
from rich.console import Console

def print_coverage_comparison(gcov, pcov, exp_file):
    console = Console()
    covered = []
    # Read exp file:
    with open(exp_file, 'r') as f:
        lines = f.readlines()
        
    for i, line in enumerate(lines, start=1):
        gc = i in gcov
        pc = i in pcov
    #    - Print tcas.c with highlights
	# - White, run by both
	# - Gray, run by none
	# - Green run by gcov not by proofocv
	# - Red run by proofcov not by gcob (Strange!) 
        line = line.rstrip('\n')
        if 'void main' in line:
            console.print(line)
        elif i in pcov and i not in gcov:
            console.print(f'[white]{i:03d}:[red]{line}')
        elif i not in pcov and i in gcov:
            console.print(f'[white]{i:03d}:[green]{line}')
        elif i not in pcov and i not in gcov:
            console.print(f'[white]{i:03d}:[bright_black]{line}')
        elif i in pcov and i in gcov:
            console.print(f'[white]{i:03d}:[white]{line}')
        else:
            assert(False)
 

def write_experiment_file(inputs, output, exp_no):
    # Assign inputs to variables
    input_lines = []
   
    input_lines.append(f"int Cur_Vertical_Sep             = {inputs[0]};\n")
    input_lines.append(f"int High_Confidence              = {inputs[1]};\n")
    input_lines.append(f"int Two_of_Three_Reports_Valid   = {inputs[2]};\n")
    input_lines.append(f"int Own_Tracked_Alt              = {inputs[3]};\n")
    input_lines.append(f"int Own_Tracked_Alt_Rate         = {inputs[4]};\n")
    input_lines.append(f"int Other_Tracked_Alt            = {inputs[5]};\n")
    input_lines.append(f"int Alt_Layer_Value              = {inputs[6]};\n")
    input_lines.append(f"int Up_Separation                = {inputs[7]};\n")
    input_lines.append(f"int Down_Separation              = {inputs[8]};\n")
    input_lines.append(f"int Other_RAC                    = {inputs[9]};\n")
    input_lines.append(f"int Other_Capability             = {inputs[10]};\n")
    input_lines.append(f"int Climb_Inhibit                = {inputs[11]};\n")
    input_lines.append("")  # blank line before return
    
    # Copy tcas_template.c to tmp/exp_##.c with inputs, with ## being exp_no
    template_path = 'tcas_template.c'
    out_path = f'tmp/exp_{exp_no:03d}.c'
    with open(template_path, 'r') as f:
        template_lines = f.readlines()
 
    # Replace INPUT and OUTPUT markers
    output_lines = []
    for l in template_lines:
        if '// INPUT' in l:
            output_lines.extend(input_lines)
        elif '// OUTPUT' in l:
            output_lines.append(f"assert(alt_sep == {int(output)});\n")
            # output_lines.append(f"assert(alt_sep == {int(output) + 1});\n")
        else:
            output_lines.append(l)
            
    # Print output file 
    with open(out_path, 'w') as f:
        for line in output_lines:
            f.write(line)
    
    return out_path
    

def run_gcov(exp_file):
    # Run gcov on the given experiment file
    import os
    import subprocess
    
    # First compile with coverage options, output to tmp/exp_###
    gcc_cmd = ["gcc", "-fprofile-arcs", "-ftest-coverage", "-o", exp_file.replace('.c', ''), exp_file]
    print("  Compiling with gcov:", ' '.join(gcc_cmd))
    subprocess.run(gcc_cmd, check=True)
   
    # Clear existing profile data files
    gcda_file = exp_file.replace('.c', '.gcda')
    gcov_file = exp_file.replace('.c', '.gcov')
    if os.path.exists(gcda_file):
        os.remove(gcda_file)
    if os.path.exists(gcov_file):
        os.remove(gcov_file)
    
    # Then run the compiled program
    run_cmd = [exp_file.replace('.c', '')]
    print("  Running experiment:", ' '.join(run_cmd))
    subprocess.run(run_cmd, check=True)
   
    # Finally run gcov to generate coverage data , send to stdout and capture
    gcov_cmd = ["gcov", "-c", "-t", exp_file]
    print("  Running gcov:", ' '.join(gcov_cmd))
    result = subprocess.run(gcov_cmd, check=True, capture_output=True, text=True)
    log_path = exp_file.replace('.c', '.gcov')
    with open(log_path, 'w') as log_file:
        log_file.write(result.stdout)
    print("  gcov log written to:", log_path)
    
    # Parse gcov output to create list of covered lines, e.g., lines executed at least once:
    # We construct a list of all line numbers that were executed at least once
    covered_lines = []
    for line in result.stdout.splitlines():
        if line.startswith("    -:") or line.startswith("#####"):
            continue  # not executed
        if line.startswith("    "):
            parts = line.split(":")
            if len(parts) >= 3:
                count_str = parts[0].strip()
                line_no_str = parts[1].strip()
                try:
                    # Count can end with '*', e.g., '12*' for branches
                    if count_str.endswith('*'):
                        count_str = count_str[:-1]
                    count = int(count_str)
                    line_no = int(line_no_str)
                    if count > 0:
                        covered_lines.append(line_no)
                except ValueError:
                    continue
    return covered_lines    
   
def run_proofcov(exp_file):
    # Run proofcov on the given experiment file
    import subprocess
    
    proofcov_cmd = ["python3", "../proofcov/proofcov.py", exp_file]
    print("  Running proofcov:", ' '.join(proofcov_cmd))
    result = subprocess.run(proofcov_cmd, check=True, capture_output=True, text=True)
    # Extract covered lines from output
    for line in result.stdout.splitlines():
        if "COVERED:" in line:
            # Conver to python list of integers
            numbers = list(map(int, line.split("COVERED:")[1].strip().split(' ')))
            return numbers
    assert(False)

def run_params(param_string, exp_no):
    values = param_string.strip().split(' ')
    inputs = values[0:-1]
    output = values[-1]
    print(f'Experiment {exp_no}:')
    print(f'  inputs: {inputs}, output: {output}')
    
    # Create experiment file
    exp_file = write_experiment_file(inputs, output, exp_no)
    print("  Experiment file created:", exp_file) 
   
    # Run gcov on the experiment file
    gcov = run_gcov(exp_file) 
    pcov = run_proofcov(exp_file)
    
    print("GCOV:", ' '.join(map(str, gcov)))
    print("PCOV:", ' '.join(map(str, pcov)))
    
    # print_coverage_comparison(gcov, pcov, exp_file)  
    return gcov, pcov 

# Main function
if __name__ == "__main__":
    param_file = 'params.txt'
    # Read command line parameter
    import sys
    args = sys.argv
    print(args)
    start = int(args[1])
    end = int(args[2])
   
    cur_exp = 0
   
    gcov = set()
    pcov = set()
     
    # Read param lines from file
    with open(param_file, 'r') as f:
        param_lines = f.readlines()
    for param_line in param_lines[start:end]:
        g, p = run_params(param_line, cur_exp)
        print("setg:", set(g))
        gcov = gcov.union(set(g))
        pcov = pcov.union(set(p))
        cur_exp += 1
        
    print_coverage_comparison(list(gcov), list(pcov), f'tmp/exp_{cur_exp-1:03d}.c')