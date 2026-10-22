from pycparser import c_parser, c_ast
from rich import print
from rich.panel import Panel
from goto import *
from normalize import UnsupportedError


class SSANames():
    def __init__(self):
        self.names = set()
        self.current = {} 
        self.next = {}

    def add(self, name):
        assert(not name in self.names)
        self.names.add(name)
        self.current[name] = 0
        self.next[name] = 1
        return self.use(name)
        
    def use(self, name):
        assert(name in self.names)
        
        return name + '.' + str(self.current[name])

    def inc(self, name):
        assert(name in self.names)
        self.current[name] = self.next[name]
        self.next[name] += 1
         
        return self.use(name)

    def copy_current(self):
        return self.current.copy()

    def count(self, name):
        assert(name in self.names)
        return self.next[name]

    def __str__(self):
        return '\n'.join(k + ": " + str(self.current[k]) for k in self.names)

    
class CParser():
    def parse_lines(lines):
        c_code = '\n'.join(lines)
        # Create a parser object
        parser = c_parser.CParser()

        # Parse the C code
        ast = parser.parse(c_code)
        return ast

    next_id = 0

    def gen_label(prefix):
        l = prefix + "_" + str(CParser.next_id)
        CParser.next_id += 1
        return l


    def handle_if(src_line, cond, iftrue, iffalse, ssa, ssa_current_before, ssa_false, ssa_true, false_writes, true_writes):
        btrue = CParser.gen_label("iftrue")
        bafter = CParser.gen_label("ifafter")
        lines = []
        lines.append(JumpIf(cond, btrue, src_line))

        for l in iffalse:
            lines.append(l)
        lines.append(Jump(bafter, src_line))

        lines.append(Label(btrue, src_line))
        for l in iftrue:
            lines.append(l)
        lines.append(Label(bafter, src_line))

        # We only need PHI nodes for variables which have
        # been declared before the if, i.e., the ssa current before:
        for v in ssa_current_before.keys():
            if not v in false_writes and not v in true_writes:
                continue
           
            iff, ift = v + '.' + str(ssa_current_before[v]), v + '.' + str(ssa_current_before[v])
            if v in false_writes:
                iff = v + '.' + str(ssa_false[v]) # TODO: this should be handled by SSANames
                
            if v in true_writes:
                ift = v + '.' + str(ssa_true[v]) # TODO: this should be handled by SSANames
                
            var = ssa.inc(v)
            CParser.assigned[var] = CParser.select(cond, CParser.assigned[ift], CParser.assigned[iff])
            lines.append(Phi(var, cond, ift, iff, src_line))
        return lines

    # Whether a variable is assigned after (cond ? a_true : a_false), where each of a_true and
    # a_false is True, False or a condition
    def select(cond, a_true, a_false):
        if a_true is a_false and isinstance(a_true, bool):
            return a_true
        parts = []
        for c, a in ((cond, a_true), (Not(cond), a_false)):
            if a is True:
                parts.append(c)
            elif a is not False:
                parts.append(And(c, a))
        return parts[0] if len(parts) == 1 else Or(parts[0], parts[1])

    # GOTO expressions which are truth values
    BOOLEAN = (Eq, Ne, Gt, Ge, Lt, Le, And, Or, Not)

    # C allows a number as a truth value (if (x), !x, x && y), meaning x != 0.
    # Conditions in the GOTO language are always truth values, so the comparison is made explicit.
    def as_condition(e):
        if isinstance(e, CParser.BOOLEAN):
            return e
        return Ne(e, Constant('0'))

    # The other direction, a truth value used as a number (e.g. x = (a > b);), is not supported
    def as_number(e, c_expr):
        if isinstance(e, CParser.BOOLEAN):
            raise UnsupportedError(f"Unsupported: condition used as a number at line {c_expr.coord.line}")
        return e

    def handle_expr(e, ssa):
        if isinstance(e, c_ast.BinaryOp):
            lhs = CParser.handle_expr(e.left, ssa)
            rhs = CParser.handle_expr(e.right, ssa)
            if e.op in ('&&', '||'):
                lhs, rhs = CParser.as_condition(lhs), CParser.as_condition(rhs)
            else:
                lhs, rhs = CParser.as_number(lhs, e.left), CParser.as_number(rhs, e.right)

            if e.op == '==':
                return Eq(lhs, rhs)
            elif e.op == '!=': 
                # Consider if this should be Not(Eq(lhs, rhs))
                return Ne(lhs, rhs)
            elif e.op == '>':
                return Gt(lhs, rhs)
            elif e.op == '>=':
                return Ge(lhs, rhs)
            elif e.op == '<':
                return Lt(lhs, rhs)
            elif e.op == '<=':
                return Le(lhs, rhs)
            elif e.op == '+':
                return Add(lhs, rhs)
            elif e.op == '-':
                return Sub(lhs, rhs)
            elif e.op == '*':
                return Mul(lhs, rhs)
            elif e.op == '&&':
                return And(lhs, rhs)
            elif e.op == '||':
                return Or(lhs, rhs)
            elif e.op == '%':
                CParser.errors.append((list(CParser.path), Eq(rhs, Constant('0'))))
                return Mod(lhs, rhs)
            elif e.op == '/':
                CParser.errors.append((list(CParser.path), Eq(rhs, Constant('0'))))
                return Div(lhs, rhs)
            else:
               raise TypeError(f"Unsupported binop: {e.op}")
        elif isinstance(e, c_ast.ID):
            name = ssa.use(e.name)
            assigned = CParser.assigned[name]
            if assigned is not True:
                # Reading a variable which might not be assigned is an error
                CParser.errors.append((list(CParser.path), None if assigned is False else Not(assigned)))
            return Var(name)
        elif isinstance(e, c_ast.Constant):
            return Constant(e.value)
        elif isinstance(e, c_ast.UnaryOp):
            if e.op == '-':
                hs = CParser.as_number(CParser.handle_expr(e.expr, ssa), e.expr)
                return Neg(hs)
            elif e.op == '!':
                hs = CParser.as_condition(CParser.handle_expr(e.expr, ssa))
                return Not(hs)
            else:
               raise TypeError(f"Unsupported UnaryOp: {e.op}")
        else:
            raise TypeError(f"Unsupported expr: {e}")

    def handle_call(c, ssa):
        name = c.name.name
        if name == "assert":
            args = c.args.exprs
            assert(len(args) == 1)
            expr = CParser.as_condition(CParser.handle_expr(args[0], ssa))
            return Assert(expr, c.coord.line)
        else:
            raise TypeError(f"Unsupported call: {c}")

    # Returns list of stmts and set of changed variables
    def handle_stmt(s, ssa):
        if isinstance(s, c_ast.FuncCall):
            return [CParser.handle_call(s, ssa)], set()
        elif isinstance(s, c_ast.Return):
            return [Return(CParser.as_number(CParser.handle_expr(s.expr, ssa), s.expr), s.coord.line)], set()
        elif isinstance(s, c_ast.If):
            cond = CParser.as_condition(CParser.handle_expr(s.cond, ssa))
           
            # We save the current SSA using state before branching
            ssa_current_before = ssa.copy_current()
            CParser.path.append(Not(cond))
            iffalse, false_writes = CParser.handle_stmt(s.iffalse, ssa)
            CParser.path.pop()
             
            # Now ssa might have increased both current and next
            # we need to restore uses before handling iftrue
            # We must save the current to use it for PHI nodes
           
            ssa_false_current = ssa.copy_current() 
            
            ssa.current = ssa_current_before.copy()
            CParser.path.append(cond)
            iftrue, true_writes = CParser.handle_stmt(s.iftrue, ssa)
            CParser.path.pop()
            ssa_true_current = ssa.copy_current()
        
            ssa.current = ssa_current_before.copy()
            
            # But we need to add all writes from both branches to the current
            return CParser.handle_if(s.coord.line, 
                                     cond, 
                                     iftrue, 
                                     iffalse, 
                                     ssa, 
                                     ssa_current_before, 
                                     ssa_false_current, 
                                     ssa_true_current, 
                                     false_writes, 
                                     true_writes), false_writes.union(true_writes)
           
        elif isinstance(s, c_ast.Compound):
            if not s.block_items:
                return [], set()

            items = []
            all_changed = set()
            for s in s.block_items:
                ret, changed_vars = CParser.handle_stmt(s, ssa)
                all_changed = all_changed.union(changed_vars)
                items = items + ret
            return items, all_changed
        elif isinstance(s, c_ast.Decl):
            name = s.name
            dectype = s.type.type.names[0]
            assert(dectype == 'int')
            if isinstance(s.init, c_ast.FuncCall):
                assert(s.init.name.name == 'nondet_int')
                # An input: assigned, with any value
                CParser.assigned[ssa.add(name)] = True
                return [Declaration(ssa.use(name), None, s.coord.line)], {name}
            else:
                if isinstance(s.init, c_ast.Constant):
                    CParser.assigned[ssa.add(name)] = True
                    return [Declaration(ssa.use(name), s.init.value, s.coord.line)], {name}
                elif isinstance(s.init, c_ast.UnaryOp):
                    assert(s.init.op == '-')
                    assert(isinstance(s.init.expr, c_ast.Constant))
                    value = s.init.expr.value
                    CParser.assigned[ssa.add(name)] = True
                    return [Declaration(ssa.use(name), '-' + value, s.coord.line)], {name}
                elif not s.init:
                    # Not initialized, as in C
                    CParser.assigned[ssa.add(name)] = False
                    return [Declaration(ssa.use(name), None, s.coord.line)], {name}
                else:
                    print(s.init)
                    raise Exception("Mathc on type ... ")
        elif isinstance(s, c_ast.Assignment):
            op = s.op
            assert(op == '=')
            rhs = CParser.as_number(CParser.handle_expr(s.rvalue, ssa), s.rvalue)
            assert(isinstance(s.lvalue, c_ast.ID))
            lhs = Var(ssa.inc(s.lvalue.name))
            CParser.assigned[lhs.name] = True

            return [Assignment(lhs, rhs, s.coord.line, CParser.tags.get(s))], set([s.lvalue.name])
        elif isinstance(s, c_ast.For):
            raise NotImplementedError("For loops are not supported yet, please unroll them manually")
        else:
            return [Skip()], set()
            raise TypeError(f"Unsupported statement: {s}")

    def handle_fundef(node, ssa):
        name = node.decl.name
        args = []
        if node.decl.type.args:
            for a in node.decl.type.args.params:
                n, t = a.name, a.type.type.names[0]
                assert(t == 'int')
                args.append((ssa.add(n), t))
                CParser.assigned[ssa.use(n)] = True

        stmts = []
        changed_vars = set()   
        for s in node.body:
            ret, changed = CParser.handle_stmt(s, ssa)
            changed_vars = changed_vars.union(changed)
            stmts = stmts + ret

        # Assert-C programs end with a single assert (only a return may follow it)
        asserts = [i for i, l in enumerate(stmts) if isinstance(l, Assert)]
        if len(asserts) != 1 or any(not isinstance(l, (Return, Skip)) for l in stmts[asserts[0] + 1:]):
            raise UnsupportedError("Unsupported: the program must end with a single assert")
        stmts[asserts[0]].errors = CParser.errors

        return Function(name, args, stmts), changed_vars

    def handle_node(node, ssa):
        if isinstance(node, c_ast.FuncDef):
            # Here we throw away the changed variables
            fun, _ = CParser.handle_fundef(node, ssa)
            return fun
        elif isinstance(node, c_ast.Typedef):
            #TODO: if we do not care about types this can be ignored
            return None
        elif isinstance(node, c_ast.Decl):
            #TODO: if we do not care about types this can be ignored
            return None
        else:
            raise NotImplementedError("Unsupported node type in AST" + str(type(node)))

    # Outcome tags ("true"/"false") of generated assignments, see normalize.py
    tags = {}

    # Conditions of the enclosing branches of the statement being translated
    path = []
    # Errors of the program as (path condition, error condition), see Assert
    errors = []
    # Whether each SSA variable is assigned: True, False or a condition
    assigned = {}

    def ast_to_goto(ast, tags=None):
        CParser.tags = tags if tags is not None else {}
        CParser.path = []
        CParser.errors = []
        CParser.assigned = {}
        gotos = []
        ssas = []
        for a in ast:
            ssa = SSANames()
            n = CParser.handle_node(a, ssa)
            if n:
                gotos.append(n)
                ssas.append(ssa)

        assert(len(gotos) == 1)
        return gotos[0], ssas[0]
