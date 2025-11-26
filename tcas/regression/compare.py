#!/usr/bin/env python3
import subprocess

INPUT_LINES = [
    "1258 1 0 897 174 7253 1 629 500 0 0 1",
    "867 1 1 1774 101 2204 0 499 499 1 0 1",
    "775 1 1 942 311 1504 1 540 500 1 0 1",
    "1206 1 0 5140 355 730 2 980 693 2 2 0",
    "675 1 0 300 599 424 2 700 640 1 0 1",
    "700 1 1 400 300 600 2 100 500 0 1 1",
    "906 0 0 4284 439 111 2 740 740 0 1 1",
    "798 1 1 2071 49 307 0 849 904 1 2 0",
    "799 0 1 5588 485 211 0 399 499 0 0 1",
    "934 1 1 233 500 335 0 845 400 0 1 1",
    "907 1 0 560 342 601 3 961 399 2 2 1",
    "830 1 0 -1 473 631 3 22 0 0 2 1",
    "709 1 1 686 483 672 1 465 475 1 2 1",
    "698 1 0 3071 59 307 0 849 904 0 2 0",
    "901 1 1 502 200 503 0 401 400 0 1 1",
    "652 1 0 -100 478 779 0 356 371 -1 2 0",
    "901 1 1 502 200 503 0 401 400 0 1 0",
    "718 1 0 717 34 1153 2 429 326 0 0 1",
    "718 1 0 717 34 1153 2 429 326 0 0 0",
]

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

def main():
    for i, line in enumerate(INPUT_LINES, start=1):
        args = [tok for tok in line.split() if tok]

        rc1, out1, err1 = run_tool("./tcas", args)
        rc2, out2, err2 = run_tool("./tcas_orig", args)

        if rc1 != 0 or rc2 != 0:
            print(f"LINE {i}: EXECUTION_ERROR")
            if rc1 != 0:
                print(f"  tacs rc={rc1} stderr='{err1}' input='{line}'")
            if rc2 != 0:
                print(f"  tacs_orig rc={rc2} stderr='{err2}' input='{line}'")
            continue

        try:
            v1 = parse_output_to_int(out1)
        except Exception as e:
            print(f"LINE {i}: PARSE_ERROR tacs output='{out1}' reason={e}")
            continue

        try:
            v2 = parse_output_to_int(out2)
        except Exception as e:
            print(f"LINE {i}: PARSE_ERROR tacs_orig output='{out2}' reason={e}")
            continue

        if v1 != v2:
            print(f"LINE {i}: MISMATCH input='{line}' tacs={v1} tacs_orig={v2}")
        else:
            print(f"LINE {i}: OK value={v1}")
            print(f'WORKS={line} {v1}')

if __name__ == "__main__":
    main()