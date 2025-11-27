#!/usr/bin/env python3
from cparser import CParser
from rich import print
from rich.panel import Panel
from bmc import BMC
from goto import *
from grapher import make_graph

import re
from collections import defaultdict
from rich.console import Console

import os
import sys


# What we want do to is the folllwing:
# 1. Take a C file and parse it
#    ... assume it contains a single (main) function
#    ... assume it ends with a single assert statement
# 2. Convert file to goto code
# 3. Convert goto code to BMC formula
# 4. Run BMC on the formula
# 5. If BMC returns a core, extract the lines and subexpressions
# 6. Find each line which is used by the core and mark it
# 7. Output original code with each unmarked line removed (i.e., commented)

def split_path(file_path):
    dirpath, filename = os.path.split(file_path)
    return dirpath, filename

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
print("\[proofcov] Opening file", dirpath + "/" + filename)

if not os.path.exists(dirpath + '/' + filename):
    print(f"[red]Error: File '{filename}' does not exist in directory '{dirpath}'[/red]")
    sys.exit(1)


lines = open(dirpath + '/' + filename, 'r').readlines()

# Remove trailing newlines
lines = [line.rstrip('\n') for line in lines]
def replacer(match):
    s = match.group(0)
    if s.startswith('/'):
        return " " # note: a space and not an empty string
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


# Remove empty lines
# lines = [line + '\n' for line in lines.split('\n') if line.strip() != '']

lines_with_numbers = [f"{i+1}: {line}" for i, line in enumerate(lines)]
if args.verbose:
    print(Panel.fit('\n'.join(lines_with_numbers), title="C code"))

# 2. Convert file to goto code
ast = CParser.parse_lines(lines) 

# Create CFG
graph = make_graph(ast)

# Extract filename of input file and replace .c with .png
if args.graph:
    cfg_image_path = filename.rsplit('.', 1)[0] + ".png"
    print("Generating control flow graph at tmp/" + cfg_image_path)
    graph.draw("tmp/" + cfg_image_path)

branches = None
if args.branch:
    branches = []
    branch_nodes = graph.all_branch_nodes()
    for bn in branch_nodes:
        branches.append((bn, bn.then_nodes))
        if bn.else_nodes:
            branches.append((bn, bn.else_nodes))

goto, ssa = CParser.ast_to_goto(ast)

if args.verbose:
    print(Panel.fit("[green]Goto code:[/green]"))
    print(goto)

# 3. Convert goto code to BMC formula
formula, annotated_nodes = BMC.gen_formula(goto, ssa)

if args.verbose:
    print(Panel.fit("[purple]SMT formula:[/purple]"))
    print(formula)

# 4. Run BMC on the formula
sat = BMC.check_sat(formula)

if (sat):
    print("Test [red]fail")
    sys.exit(1)

# 5. If BMC returns a core, extract the lines and subexpressions
result = BMC.get_core(formula)
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
console = Console()

if args.experiment:
    # In experiment mode we just output the marked lines as a list
    print("COVERED:", ' '.join(map(str, sorted(original_marked_lines))))
    sys.exit(0)

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
    # Retrieve number of lines from graph
    total_lines = len(graph.all_nodes())
    covered_lines = len(covered)
    print(f"Line coverage: {covered_lines}/{total_lines} ({(covered_lines/total_lines)*100:.2f}%)")
    
    if args.graph:
        cfg_image_path = filename.rsplit('.', 1)[0] + "_line.png"
        print("Generating control flow graph (line coverage) at tmp/" + cfg_image_path)
        graph.draw("tmp/" + cfg_image_path, covered)


            
if args.branch:
    total_branches = len(branches)
    covered_branches = 0
    if args.verbose:    
        print(Panel.fit("[yellow]Branch coverage details:[/yellow]"))
    for bn, nodes in branches:
        covered = False
        if args.verbose:    
            console.print(f'[white]Branch at line {bn.line_number} with target join at line {bn.target_join.line_number if bn.target_join.line_number else "N/A"}[/white]')
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
    print(f"Branch coverage: {covered_branches}/{total_branches} ({(covered_branches/total_branches)*100:.2f}%)")
    
    
if args.all and args.verbose:
    # Print summary of both coverage
    print(Panel.fit("[yellow]Coverage summary:[/yellow]"))
    print(f"Line coverage: {covered_lines}/{total_lines} ({(covered_lines/total_lines)*100:.2f}%)")
    print(f"Branch coverage: {covered_branches}/{total_branches} ({(covered_branches/total_branches)*100:.2f}%)")