#!/usr/bin/env python3
from goto import *
import subprocess
import re

class BMC():

    subexpr_count = {}

    def make_assert(line):
        return ["(assert (! " + b + " :named line" + str(line.src_line) + "." + str(i) + ")) ; line " + str(line.src_line) for i, b in enumerate(line.to_bmc())]


    # This is used to track the usage of subexpressions in if-statements (e.g., in if (a && b) we can slice away only a or b).
    # Returns name, constraints, number of created exprs, annotated AST - name of top-level subexpr and constraints required
    def create_subexprs(l, line, count=0):
        # print("-->create(" + str(l) + ")")
        if isinstance(l, BinOp):
            lhs_node, lhs_constraints, lhs_created, annotated_lhs = BMC.create_subexprs(l.lhs, line, count)
            rhs_node, rhs_constraints, rhs_created, annotated_rhs = BMC.create_subexprs(l.rhs, line, count + lhs_created)
            # print("Binop:", l)
            node_name = "subexpr_" + str(line) + "_" + str(count + lhs_created + rhs_created)
            if node_name in BMC.subexpr_count:
                BMC.subexpr_count[node_name] += 1
                node_name = node_name + "x" + str(BMC.subexpr_count[node_name])
            else:
                BMC.subexpr_count[node_name] = 0
            l.lhs = lhs_node
            l.rhs = rhs_node
            #TODO: only Bool types
            decl = "(declare-fun " + node_name + " () (Bool))"
            constraint = "(assert (! (= " + node_name + " " + l.to_bmc() + ") :named name_" + node_name + "))"

            l.lhs = annotated_lhs
            l.rhs = annotated_rhs

            annotated = l
            annotated.subexpr = node_name
            # print("\t", node_name, constraint)
            return Var(node_name), lhs_constraints + rhs_constraints + [decl, constraint], lhs_created + rhs_created + 1, annotated
        elif isinstance(l, Var):
            l.subexpr = None
            return l, [], 0, l
        elif isinstance(l, Constant):
            l.subexpr = None
            return l, [], 0, l
        else:
            assert(False)

    def print_node(n, depth=0):
        if isinstance(n, BinOp):
            print('\t'*depth, n.op, "(", n.subexpr, ")")
            BMC.print_node(n.lhs, depth+1)
            BMC.print_node(n.rhs, depth+1)
        elif isinstance(n, Var):
            print('\t'*depth, n)
        elif isinstance(n, Constant):
            print('\t'*depth, n)
        else:
            assert(False)

        # if n.lhs:
            # print_node(lhs, depth+1)

    # So if we handle l, we also want to be able to display the coverage
    def handle_phi(l):
       # TODO: we assume one expr per line ...
       count = 0
    #    node, constraints, count, annotated = BMC.create_subexprs(l.cond, l.src_line)
    #    print("Handling phi:", l, "=>", node, constraints)
    #    print(node)
    #    for c in constraints:
        #    print(c)
    #    l.cond = node
    #    BMC.print_node(annotated)
    #    return constraints + ["(assert " + l.to_bmc()[0] +")", "(assert " + l.to_bmc()[1] +")"], (annotated, l.src_line)
       return ["(assert " + l.to_bmc()[0] +")", "(assert " + l.to_bmc()[1] +")"], ([], l.src_line)

    def gen_formula(goto, ssa):
        assert(isinstance(goto, Function))
        # Turn each arg into declaration
        decls = [Declaration(a[0], -1) for a in goto.args]
        lines = decls + goto.body

        header = []
        for k in ssa.names:
            for i in range(ssa.count(k) + 1):
                n = k + "." + str(i)
                header.append("(declare-fun " + n + " () (Int))")

        constraints = []
        annotated_nodes = []
        verbose = False
        for l in lines:
            if verbose:
                print("¬", l)
            if isinstance(l, Declaration):
                if l.value:
                    constraints += BMC.make_assert(l)
                else:
                    if verbose:
                        print("\tIgnoring declaration with no value/nondet")
            elif isinstance(l, JumpIf):
                if verbose:
                    print("\tIgnoring JumpIf")
            elif isinstance(l, Assignment):
                asrt = BMC.make_assert(l)
                if verbose:
                    print("\tAssignment:", l, "=>", asrt)
                constraints += asrt
            elif isinstance(l, Jump):
                if verbose:
                    print("\tIgnoring Jump")
            elif isinstance(l, Label):
                if verbose:
                    print("\tIgnoring Label")
            elif isinstance(l, Phi):
                cons, annotated_node = BMC.handle_phi(l)
                constraints += cons
                annotated_nodes.append(annotated_node)
                if verbose:
                    print("\tPhi:", l, "=>", asrt)
            elif isinstance(l, Assert):
                asrt = BMC.make_assert(l)
                if verbose:
                    print("\tAssert:", l, " => ", asrt)
                constraints += asrt
            elif isinstance(l, Assume):
                asrt = BMC.make_assert(l)
                if verbose:
                    print("\tAssume:", l, " => ", asrt)
                constraints += asrt
            elif isinstance(l, Skip):
                if verbose:
                    print("\tIgnoring Skip")
            else:
               raise TypeError(f"Unsupported Line: {l}")

        footer = []
        footer.append("(check-sat)")

        all = []

        for h in header:
            all.append(h)
        for c in constraints:
            all.append(c)
        for f in footer:
            all.append(f)

        return '\n'.join(all) + '\n', annotated_nodes


    def run_z3(formula):
        smtfile = "tmp.smt2"
        fout = open(smtfile, 'w')
        fout.write(formula)
        fout.close()
        command = ["z3", smtfile]
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = result.stdout.decode('utf-8'), result.stderr.decode('utf-8')

        if stderr:
            print("STDERR")
            print(stderr)

        return stdout

    # True iff SAT
    def check_sat(formula):

        stdout = BMC.run_z3(formula)

        if "unsat" in stdout:
            return False
        elif "sat" in stdout:
            return True
        else:
            print("What is output: ", )
            print("STDOUT\n", stdout)
            assert(False)

    def get_model(formula):
        stdout = BMC.run_z3(formula + "\n(get-model)")

    def get_core(formula):
        stdout = BMC.run_z3("(set-option :produce-unsat-cores true)\n(set-option :smt.core.minimize true)\n" + formula + "\n(get-unsat-core)")
        p = r"line(\d+)\.(\d+)"
        r = re.findall(p, stdout)
        lines = set()
        for m in r:
            lines.add(int(m[0]))

        p = r"name_subexpr_(\d+)_(\d+)"
        r = re.findall(p, stdout)
        for m in r:
            lines.add(int(m[0])) # We throwaway the second number, as we only care about the line number
            # lines.add((int(m[0]), int(m[1])))
        return lines
