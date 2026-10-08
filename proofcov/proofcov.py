#!/usr/bin/env python3
from cparser import CParser
from rich import print
from rich.panel import Panel
from bmc import BMC
from goto import *
from grapher import make_graph
from normalize import normalize, UnsupportedError

import re
from rich.console import Console

import builtins
import os
import subprocess
import sys


# What we want do to is the folllwing:
# 1. Take a C file and parse it
#    ... assume it contains a single (main) function
#    ... assume it ends with a single assert statement
# 2. Convert file to goto code
# 3. Convert goto code to BMC formula
# 4. Run BMC on the formula
# 5. If BMC returns a core, extract the lines
# 6. Find each line which is used by the core and mark it
# 7. Output original code with each unmarked line removed (i.e., commented)

def split_path(file_path):
    dirpath, filename = os.path.split(file_path)
    return dirpath, filename

# Format e.g. "Line coverage: 3/4 (75.00%)", or "Branch coverage: 0/0 (no branches)" when there is nothing to cover
def format_coverage(kind, covered, total, unit):
    if total == 0:
        return f"{kind} coverage: 0/0 (no {unit})"
    return f"{kind} coverage: {covered}/{total} ({(covered/total)*100:.2f}%)"

# Lets use argparse for command line arguments
import argparse

# Currently one input file (c program) and an option --graph for outputing graph 
argsparser = argparse.ArgumentParser(description='Proof coverage tool for C programs.')
argsparser.add_argument('input_file', metavar='input_file', type=str, help='Path to the input C file')
# If --graph is provided, set graph to true
argsparser.add_argument('--graph', action='store_true', help='Output control flow graph as PNG')
# If --line is provided, set branch to true
argsparser.add_argument('--line', action='store_true', help='Output line coverage information')
# If --branch is provided, set branch to true
argsparser.add_argument('--branch', action='store_true', help='Output branch coverage information')
# If --all set both line and branch to true
argsparser.add_argument('--all', action='store_true', help='Output both line and branch coverage information')
# If -v or --verbose is provided, set verbose to true
argsparser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose output')
# If --experiment is provided, set experiment mode
argsparser.add_argument('--experiment', action='store_true', help='Run in experiment mode on tcas')
# If --enumerate-cores is provided, report coverage for every minimal unsat core instead of a single one
argsparser.add_argument('--enumerate-cores', action='store_true', help='Enumerate all minimal unsat cores and report coverage for each')

# If --track-undef is provided, set track_undef to true
argsparser.add_argument('--track-undef', action='store_true', help='Track undefined behavior in the analysis')

args = argsparser.parse_args()

if args.all:
    args.line = True
    args.branch = True

# 1. Take a C file and parse it (currently we do nothing, but could have preprocessing here)
file_path = args.input_file
dirpath, filename = split_path(file_path)
if not dirpath:
    dirpath = '.'
print(r"\[proofcov] Opening file", dirpath + "/" + filename)

if not os.path.exists(dirpath + '/' + filename):
    print(f"[red]Error: File '{filename}' does not exist in directory '{dirpath}'[/red]")
    sys.exit(1)


lines = open(dirpath + '/' + filename, 'r').readlines()

# Remove trailing newlines
lines = [line.rstrip('\n') for line in lines]
def replacer(match):
    s = match.group(0)
    if s.startswith('/'):
        # note: a space and not an empty string, and keep the newlines of a /* */ comment so line numbers stay the same
        return " " + "\n" * s.count("\n")
    else:
        return s
comment_pattern = re.compile(
    r'//.*?$|/\*.*?\*/|\'(?:\\.|[^\\\'])*\'|"(?:\\.|[^\\"])*"',
    re.DOTALL | re.MULTILINE
)

# Remove includes
newlines = []
for l in lines:
    if "#include" in l:
        newlines.append("//" + l)
    else:
        newlines.append(l)
        
lines = newlines

# We change main declaration for coverage and ignore its arguments
# So we replace int main(int argc, char *argv[]) {  -->  void main() {
main_pattern = re.compile(r'\bint\s+main\s*\(\s*int\s+argc\s*,\s*char\s*\*\s*argv\s*\[\s*\]\s*\)\s*{')
lines = [main_pattern.sub('void main() {', line) for line in lines]

# Remove comments
lines = re.sub(comment_pattern, replacer, '\n'.join(lines)).split('\n')


lines_with_numbers = [f"{i+1}: {line}" for i, line in enumerate(lines)]
if args.verbose:
    print(Panel.fit('\n'.join(lines_with_numbers), title="C code"))

# Expand preprocessor directives (#define) with the C preprocessor, its line markers keep the original line numbers
source = '\n'.join(lines)
if re.search(r'^\s*#', source, re.MULTILINE):
    cpp = subprocess.run(["gcc", "-E", "-x", "c", "-"], input=source, capture_output=True, text=True)
    if cpp.returncode != 0:
        print(cpp.stderr, file=sys.stderr)
        sys.exit(2)
    source = cpp.stdout

# 2. Convert file to goto code, after rewriting it into the supported subset (see normalize.py)
ast = CParser.parse_lines(source.split('\n'))
try:
    ast, tags = normalize(ast)
except UnsupportedError as e:
    print(f"Unsupported: {e}" if not str(e).startswith("Unsupported") else str(e), file=sys.stderr)
    sys.exit(2)

# Create CFG
graph = make_graph(ast)

# Extract filename of input file and replace .c with .png
if args.graph:
    cfg_image_path = filename.rsplit('.', 1)[0] + ".png"
    print("Generating control flow graph at tmp/" + cfg_image_path)
    graph.draw("tmp/" + cfg_image_path)

# Branches are identified by the line of their if-statement and the side (then/else), so the
# copies of an if in a function inlined several times count as one branch
branches = None
if args.branch:
    branches = {}
    branch_nodes = graph.all_branch_nodes()
    for bn in branch_nodes:
        if bn.then_nodes:
            branches.setdefault((bn.line_number, "then"), []).append((bn, bn.then_nodes))
        if bn.else_nodes:
            branches.setdefault((bn.line_number, "else"), []).append((bn, bn.else_nodes))

goto, ssa = CParser.ast_to_goto(ast, tags)

if args.verbose:
    print(Panel.fit("[green]Goto code:[/green]"))
    print(goto)

# 3. Convert goto code to BMC formula
formula = BMC.gen_formula(goto, ssa, track_undef=args.track_undef)

if args.verbose:
    print(Panel.fit("[purple]SMT formula:[/purple]"))
    print(formula)

# 4. Run BMC on the formula
if args.enumerate_cores:
    # 5. Enumerate all minimal unsat cores (none means the formula is SAT)
    cores = BMC.get_all_cores(formula)
    if not cores:
        print("Test [red]fail")
        sys.exit(1)
else:
    sat = BMC.check_sat(formula)

    if (sat):
        print("Test [red]fail")
        sys.exit(1)

    # 5. If BMC returns a core, extract the lines
    cores = [BMC.get_core(formula)]

console = Console()

if args.experiment:
    # In experiment mode we just output the marked lines of each core as a list, followed by the
    # outcomes (line:true/false) of the statements generated from truth values and ?: in the core.
    # STATEMENT_LINES are all lines with a statement, OUTCOME_LINES those with generated outcomes.
    # (builtins.print, as rich's print wraps long lines)
    for core in cores:
        builtins.print("COVERED:", ' '.join(map(str, sorted(BMC.core_to_lines(core)))))
        builtins.print("OUTCOMES:", ' '.join(f"{l}:{t}" for l, t in sorted(BMC.core_to_outcomes(core))))
    builtins.print("STATEMENT_LINES:", ' '.join(map(str, sorted({n.line_number for n in graph.all_nodes()}))))
    builtins.print("OUTCOME_LINES:", ' '.join(map(str, sorted({l.src_line for l in goto.body if getattr(l, "tag", None)}))))
    sys.exit(0)

for core_id, core in enumerate(cores, start=1):
    result = BMC.core_to_lines(core)
    if args.enumerate_cores:
        print(Panel.fit(f"[blue]Core {core_id}/{len(cores)}[/blue]"))

    if args.verbose:
        print(Panel.fit("[blue]Unsat core:[/blue]"))
        print(f"{result}")

    # 6. Find each line which is used by the core and translate back to original and mark it
    marked_lines = list(result)
    marked_lines.sort()
    original_marked_lines = marked_lines

    if args.verbose:
        print(Panel.fit("[red]Marked lines:[/red]"))
        print(f"{original_marked_lines}")

    # Write all covered lines in green and all non-covered lines in red
    if args.line:
        covered = []
        if args.verbose:
            print(Panel.fit("[yellow]Line coverage details:[/yellow]"))
        for i, line in enumerate(lines, start=1):
            if i in original_marked_lines:
                if args.verbose:    
                    console.print(f'[white]{i:03d}:[green]{line}')
                covered.append(i)
            else:
                if args.verbose:    
                    console.print(f'[white]{i:03d}:[red]{line}')
        # Display line coverage as a fraction and percentage
        # Lines with at least one statement (graph node), and those of them covered by the core.
        # Several statements on one line count as one line.
        statement_lines = {n.line_number for n in graph.all_nodes()}
        total_lines = len(statement_lines)
        covered_lines = len(statement_lines.intersection(covered))
        print(format_coverage("Line", covered_lines, total_lines, "lines"))
        
        if args.graph:
            suffix = f"_line_core{core_id}.png" if args.enumerate_cores else "_line.png"
            cfg_image_path = filename.rsplit('.', 1)[0] + suffix
            print("Generating control flow graph (line coverage) at tmp/" + cfg_image_path)
            graph.draw("tmp/" + cfg_image_path, covered)


                
    if args.branch:
        total_branches = len(branches)
        covered_branches = 0
        if args.verbose:    
            print(Panel.fit("[yellow]Branch coverage details:[/yellow]"))
        for (line_number, side), instances in sorted(branches.items()):
            covered = False
            if args.verbose:    
                console.print(f'[white]Branch at line {line_number} ({side})[/white]')
            for bn, nodes in instances:
                for n in nodes:
                    if n.line_number in original_marked_lines:
                        if args.verbose:    
                            console.print(f'  [white]Node at line {n.line_number}:[green] {n.text}[/green][/white]')
                        covered = True
                    else:
                        if args.verbose:    
                            console.print(f'  [white]Node at line {n.line_number}:[red] {n.text}[/red][/white]') 
            if covered:
                covered_branches += 1
        # Display branch coverage as a fraction and percentage
        print(format_coverage("Branch", covered_branches, total_branches, "branches"))
        
        
    if args.all and args.verbose:
        # Print summary of both coverage
        print(Panel.fit("[yellow]Coverage summary:[/yellow]"))
        print(format_coverage("Line", covered_lines, total_lines, "lines"))
        print(format_coverage("Branch", covered_branches, total_branches, "branches"))
