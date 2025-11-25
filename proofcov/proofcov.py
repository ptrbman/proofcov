#!/usr/bin/env python3
from parser import parse_file, test_to_bmc
from cparser import CParser
from rich import print
from rich.panel import Panel
from bmc import BMC
from goto import *
from unroller import unroll
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
#    ... Unroll all loops
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
args = argsparser.parse_args()

# 1. Take a C file and parse it (currently we do nothing, but could have preprocessing here)
file_path = args.input_file
dirpath, filename = split_path(file_path)
if not dirpath:
    dirpath = '.'
print("Opening file", dirpath + "/" + filename)

if not os.path.exists(dirpath + '/' + filename):
    print(f"[red]Error: File '{filename}' does not exist in directory '{dirpath}'[/red]")
    sys.exit(1)


lines = open(dirpath + '/' + filename, 'r').readlines()

# Remove trailing newlines
lines = [line.rstrip('\n') for line in lines]
print("Original lines:")
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
print(Panel.fit('\n'.join(lines_with_numbers), title="C code"))

UNROLLINGS = 10
unrolled_lines, line_map = unroll(lines, UNROLLINGS)

unrolled_lines_with_numbers = [f"{i+1}: {line}" for i, line in enumerate(unrolled_lines)]
print(Panel.fit('\n'.join(unrolled_lines_with_numbers), title="C code after unrolling loops"))

# 2. Convert file to goto code
ast = CParser.parse_lines(unrolled_lines)

# Call find_branches
graph = make_graph(ast)

# Extract filename of input file and replace .c with .png
if args.graph:
    cfg_image_path = filename.rsplit('.', 1)[0] + ".png"
    print("Generating control flow graph at tmp/" + cfg_image_path)
    graph.draw("tmp/" + cfg_image_path)

goto, ssa = CParser.ast_to_goto(ast)

print(Panel.fit("[green]Goto code:[/green]"))
print(goto)

# 3. Convert goto code to BMC formula
formula, annotated_nodes = BMC.gen_formula(goto, ssa)
print(Panel.fit("[purple]SMT formula:[/purple]"))
print(formula)

# 4. Run BMC on the formula
sat = BMC.check_sat(formula)

if (sat):
    print("Test [red]fail")
    sys.exit(1)

# 5. If BMC returns a core, extract the lines and subexpressions
result = BMC.get_core(formula)
print(Panel.fit("[blue]Unsat core:[/blue]"))
print(f"{result}")

# 6. Find each line which is used by the core and translate back to original and mark it
marked_lines = list(result)
marked_lines.sort()

# print("Marked lines:", marked_lines)
# print("Line map:", line_map)

original_marked_lines = set()

for ml in marked_lines:
    original_marked_lines.add(line_map[ml-1] + 1)
    # print(f"Marked line {ml} corresponds to original line {line_map[ml-1] + 1}")


# print(f"original_marked_lines: {original_marked_lines}")
print(Panel.fit("[red]Marked lines:[/red]"))
print(f"{original_marked_lines}")

# Write all covered lines in green and all non-covered lines in red
console = Console()
covered = []
for i, line in enumerate(lines, start=1):
    if 'void main' in line:
        console.print(line)
    elif i in original_marked_lines:
        console.print(f'[white]{i:03d}:[green]{line}')
        covered.append(i)
    else:
        console.print(f'[white]{i:03d}:[red]{line}')
       
print("COVERED: " + ' '.join(str(l) for l in covered)) 