#!/usr/bin/env python3
from goto import *
from marco import get_MUSes
import re
# Imported as a module, since z3 defines names (And, Or, Not, ...) that clash with goto
import z3

class BMC():
   
    def make_assert(line, track_undef):
        return ["(assert (! " + b + " :named line" + str(line.src_line) + "." + str(i) + ")) ; line " + str(line.src_line) for i, b in enumerate(line.to_bmc(track_undef))]

    def handle_phi(l, track_undef):
        if track_undef:
            [true_decl, true_cond, a, false_decl, false_cond, b] = l.to_bmc(track_undef)
            named_true_cond = f'(assert (! {true_cond} :named phi.if.{l.src_line}.{l.var}.cond)) ; if cond line {l.src_line}'
            
            named_a = f'(assert (! {a} :named phi.if.{l.src_line}.{l.var})) ; if line {l.src_line}'
            named_false_cond = f'(assert (! {false_cond} :named phi.else.{l.src_line}.{l.var}.cond)) ; else cond line {l.src_line}'  
            named_b = f'(assert (! {b} :named phi.else.{l.src_line}.{l.var})) ; else line {l.src_line}'
            return [true_decl, named_true_cond, named_a, false_decl, named_false_cond, named_b]
        else:
            if_line = [f'(assert (! {l.to_bmc(track_undef)[0]} :named phi.if.{l.src_line}.{l.var})) ; if line {l.src_line}', f'(assert (! {l.to_bmc(track_undef)[1]} :named phi.else.{l.src_line}.{l.var})) ; else line {l.src_line}']
            return if_line

    def gen_formula(goto, ssa, track_undef=False):
        assert(isinstance(goto, Function))
        
        # Turn each arg into declaration
        decls = [Declaration(a[0], -1) for a in goto.args]
        lines = decls + goto.body

        header = []
        for k in ssa.names:
            for i in range(ssa.count(k) + 1):
                n = k + "." + str(i)
                header.append("(declare-fun " + n + " () (Int))")
                if (track_undef):
                    # Add a special untracked flag for each variable version
                    header.append("(declare-fun " + n + ".undef () (Int))")

        constraints = []
        verbose = False
        for l in lines:
            if verbose:
                print("¬", l)
            if isinstance(l, Declaration):
                if l.value:
                    constraints += BMC.make_assert(l, track_undef)
                else:
                    if verbose:
                        print("\tIgnoring declaration with no value/nondet")
            elif isinstance(l, JumpIf):
                if verbose:
                    print("\tIgnoring JumpIf")
            elif isinstance(l, Assignment):
                asrt = BMC.make_assert(l, track_undef)
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
                constraints += BMC.handle_phi(l, track_undef)
                if verbose:
                    print("\tPhi:", l, "=>", asrt)
            elif isinstance(l, Assert):
                asrt = BMC.make_assert(l, track_undef)
                if verbose:
                    print("\tAssert:", l, " => ", asrt)
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

        return '\n'.join(all) + '\n'


    # Load a formula into a z3 solver, with every named assertion turned into an
    # assumption literal (see add_assumption_literals).
    # Returns the solver and the list of assumption literals.
    def make_solver(formula):
        solver = z3.Solver()
        literals = []
        for a in z3.parse_smt2_string(BMC.add_assumption_literals(formula)):
            # Only implications guarded by an a_ literal are assumption literals,
            # any other implication is an ordinary constraint
            if z3.is_implies(a) and a.arg(0).decl().name().startswith("a_"):
                literals.append(a.arg(0))
            solver.add(a)
        return solver, literals

    # True iff SAT
    def check_sat(formula):
        solver, literals = BMC.make_solver(formula)
        result = solver.check(literals)
        if result == z3.unknown:
            raise RuntimeError("z3 returned unknown: " + solver.reason_unknown())
        return result == z3.sat

    # Returns a (minimized) unsat core as a set of line numbers
    def get_core(formula):
        solver, literals = BMC.make_solver(formula)
        solver.set("core.minimize", True)
        assert solver.check(literals) == z3.unsat
        return BMC.core_to_lines([c.decl().name() for c in solver.unsat_core()])

    # Convert every named assertion such as:
    #     (assert (! (= x.1 1) :named line5.0)) ; line 5
    # to an assumption literal:
    #     (declare-fun a_line5.0 () Bool)
    #     (assert (=> a_line5.0 (= x.1 1)))
    # that can later be included/excluded from check-sat-assuming.
    def add_assumption_literals(formula):
        lines = formula.strip().splitlines()
        new_lines = []
        assumption_literals = []

        # Match all named assertions
        pattern = re.compile(r"\(assert\s+\(!\s*(?P<body>.*)\s*:named\s+(?P<name>[^\s\)]+)\s*\)\)")

        for line in lines:
            line = line.strip()
            if not line or line.startswith("(check-sat"):
                continue

            m = pattern.search(line)
            if m:
                body = m.group("body").strip()
                name = m.group("name").strip()
                a_name = f"a_{name}"

                new_lines.append(f"(declare-fun {a_name} () Bool)")
                new_lines.append(f"(assert (=> {a_name} {body}))")
                assumption_literals.append(a_name)
            else:
                new_lines.append(line)

        if assumption_literals:
            new_lines.append(f"(check-sat-assuming ({' '.join(assumption_literals)}))")

        return "\n".join(new_lines)

    # Takes an unsat core (list of assumption literal names) and converts it to line numbers
    def core_to_lines(core):
        lines = set()
        for c in core:
            m = re.match(r"a_line(\d+)\.\d+", c)
            if m:
                lines.add(int(m.group(1)))
                continue

            m = re.match(r"a_phi\.(\w+)\.(\d+)\.", c)
            if m:
                lines.add(int(m.group(2)))
        return lines

    # Enumerate all minimal unsat cores, each as a set of line numbers.
    # Returns an empty list if the formula is SAT.
    def get_all_cores(formula):
        muses = get_MUSes(BMC.add_assumption_literals(formula))
        return [BMC.core_to_lines(mus) for mus in muses]
