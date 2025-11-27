#!/usr/bin/env python3
import subprocess


# Read INPUT_LINES from hardcoded list small.txt
with open('universe_fixed.txt', 'r') as f:
    universe_lines = f.readlines()
    INPUT_LINES = [line.strip() for line in universe_lines if line.strip() and not line.startswith('#')]

# INPUT_LINES = [
#     "765 1 0 500 400 424 5 400 500 0 0 0"
# ]
# INPUT_LINES = [
#     "1258 1 0 897 174 7253 1 629 500 0 0 1",
#     "867 1 1 1774 101 2204 0 499 499 1 0 1",
#     "775 1 1 942 311 1504 1 540 500 1 0 1",
#     "1206 1 0 5140 355 730 2 980 693 2 2 0",
#     "675 1 0 300 599 424 2 700 640 1 0 1",
#     "700 1 1 400 300 600 2 100 500 0 1 1",
#     "906 0 0 4284 439 111 2 740 740 0 1 1",
#     "798 1 1 2071 49 307 0 849 904 1 2 0",
#     "799 0 1 5588 485 211 0 399 499 0 0 1",
#     "934 1 1 233 500 335 0 845 400 0 1 1",
#     "907 1 0 560 342 601 3 961 399 2 2 1",
#     "830 1 0 -1 473 631 3 22 0 0 2 1",
#     "709 1 1 686 483 672 1 465 475 1 2 1",
#     "698 1 0 3071 59 307 0 849 904 0 2 0",
#     "901 1 1 502 200 503 0 401 400 0 1 1",
#     "652 1 0 -100 478 779 0 356 371 -1 2 0",
#     "901 1 1 502 200 503 0 401 400 0 1 0",
#     "718 1 0 717 34 1153 2 429 326 0 0 1",
#     "718 1 0 717 34 1153 2 429 326 0 0 0",
# ]

def run_tool(tool, args):
    try:
        p = subprocess.run(
            [tool] + args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
        )
        return p.returncode, p.stdout.strip(), p.stderr.strip()
    except FileNotFoundError:
        return 127, "", f"Executable not found: {tool}"

def parse_output_to_int(s):
    toks = [t for t in s.split() if t]
    if not toks:
        raise ValueError("empty output")
    return int(toks[0])

def prepare_original():
    # Compile original tcas.c to tcas_orig
    compile_cmd = ["gcc", "-o", "tcas_orig", "tcas_original.c"]
    print("Compiling original tcas.c:", ' '.join(compile_cmd))
    subprocess.run(compile_cmd, check=True)

def prepare_template():
    # Prepare tcas.c from tcas_template.c
    with open("../proofcov_template.c", "r") as f:
        template = f.read()
        
    # We have to modify int main() to accept argc, argv
    template = template.replace("void main()", "int main(int argc, char** argv)")
    # We have to replace // INPUT with reading from argv
    input_code = """
    if (argc != 13) {
        printf("Error: Expected 12 input arguments.\\n");
        return 1;
    }
    int Cur_Vertical_Sep = atoi(argv[1]);
    int High_Confidence = atoi(argv[2]);
    int Two_of_Three_Reports_Valid = atoi(argv[3]);
    int Own_Tracked_Alt = atoi(argv[4]);
    int Own_Tracked_Alt_Rate = atoi(argv[5]);
    int Other_Tracked_Alt = atoi(argv[6]);
    int Alt_Layer_Value = atoi(argv[7]);
    int Up_Separation = atoi(argv[8]);
    int Down_Separation = atoi(argv[9]);
    int Other_RAC = atoi(argv[10]);
    int Other_Capability = atoi(argv[11]);
    int Climb_Inhibit = atoi(argv[12]);
    """
    template = template.replace("// INPUTS", input_code)
   
    # We also have to include for atoi in beginning
    template = template.replace("#include <stdio.h>", "#include <stdio.h>\n#include <stdlib.h>")  
    
    # Also replace OUTPUT with just printing alt_sep
    template = template.replace("// OUTPUT", 'printf("%d\\n", alt_sep);')    
    
    with open("tcas_template.c", "w") as f:
        f.write(template)
    
    # Compile tcas_template.c to tcas_template
    compile_cmd = ["gcc", "-o", "tcas_template", "tcas_template.c"]
    print("Compiling tcas_template.c:", ' '.join(compile_cmd))
    subprocess.run(compile_cmd, check=True)
        

def main():
    prepare_original()
    prepare_template()
    for i, line in enumerate(INPUT_LINES, start=1):
        args = [tok for tok in line.split() if tok]
        
        rc1, out1, err1 = run_tool("./tcas_template", args)
        print(f'Tcas template output: rc={rc1} out="{out1}" err="{err1}"')
        rc2, out2, err2 = run_tool("./tcas_orig", args)

        if rc1 != 0 or rc2 != 0:
            print(f"LINE {i}: EXECUTION_ERROR")
            if rc1 != 0:
                print(f"  tacs rc={rc1} stderr='{err1}' input='{line}'")
            if rc2 != 0:
                print(f"  tacs_orig rc={rc2} stderr='{err2}' input='{line}'")
            raise RuntimeError("Execution error")
            # continue

        try:
            v1 = parse_output_to_int(out1)
        except Exception as e:
            print(f"LINE {i}: PARSE_ERROR tcas_template output='{out1}' reason={e}")
            raise RuntimeError("Parse error")
            # continue

        try:
            v2 = parse_output_to_int(out2)
        except Exception as e:
            print(f"LINE {i}: PARSE_ERROR tacs_orig output='{out2}' reason={e}")
            raise RuntimeError("Parse error")
            # continue

        if v1 != v2:
            print(f"LINE {i}: MISMATCH input='{line}' tacs={v1} tacs_orig={v2}")
            raise RuntimeError("Mismatch")
        else:
            print(f"LINE {i}: OK value={v1}")
            print(f'WORKS={line} {v1}')

if __name__ == "__main__":
    main()