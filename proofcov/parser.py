#!/usr/bin/env python3

import re
from rich import print
from rich.panel import Panel
from test import Test
from cparser import *
from bmc import BMC

def split_tests(filename):
    tests = []
    current_test = []
    inside_test = False

    with open(filename, 'r') as file:
        for line in file:
            line = line.strip()
            if line == "#BEGINTEST":
                inside_test = True
                current_test = []
            elif line == "#ENDTEST":
                inside_test = False
                tests.append(current_test)
            elif inside_test:
                current_test.append(line)

    return tests

def parse_file(filename, dirpath):
    tmp_file = filename + '.tmp'
    tests = split_tests(dirpath + '/' + filename)
    tests = list(map(lambda x : Test.from_lines(x, dirpath), tests))
    return tests


def test_to_bmc(test):
    ast = CParser.parse_test(test)
    # print(ast)
    goto, ssa = CParser.ast_to_goto(ast)
    # print(goto)
    formula, annotated_nodes = BMC.gen_formula(goto, ssa)
    # print(formula, annotated_nodes)
    # assert(False)
    return formula, annotated_nodes
