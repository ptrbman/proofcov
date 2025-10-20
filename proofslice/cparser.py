from pycparser import c_parser, c_ast
from rich import print
from rich.panel import Panel
from goto import *


class SSANames():
    def __init__(self):
        self.names = set()
        self.current = {} 
        self.next = {}
        self.writes = set()

    def add(self, name):
        assert(not name in self.names)
        self.names.add(name)
        self.current[name] = 0
        self.next[name] = 1
        return self.use(name)

    def reset_writes(self):
        self.writes.clear()
        
    def use(self, name):
        assert(name in self.names)
        
        return name + '.' + str(self.current[name])

    def inc(self, name):
        assert(name in self.names)
        self.current[name] = self.next[name]
        self.next[name] += 1
        self.writes.add(name)
         
        return self.use(name)

    def copy_current(self):
        return self.current.copy()

    def count(self, name):
        assert(name in self.names)
        return self.next[name]

    def extract_name(name):
        return name.split(".")[0]

    def __str__(self):
        return '\n'.join(k + ": " + str(self.current[k]) for k in self.names)

    
class CParser():
    def parse_lines(lines):
        c_code = ''.join(lines)
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
                
            lines.append(Phi(ssa.inc(v), cond, ift, iff, src_line))
        return lines

    def handle_expr(e, ssa, cover=False):
        if isinstance(e, c_ast.BinaryOp):
            lhs = CParser.handle_expr(e.left, ssa, cover)
            rhs = CParser.handle_expr(e.right, ssa, cover)

            if e.op == '==':
                return Eq(lhs, rhs)
            elif e.op == '!=': 
                # Consider if this should be Not(Eq(lhs, rhs))
                return Ne(lhs, rhs)
            elif e.op == '>':
                return Gt(lhs, rhs)
            elif e.op == '>=':
                return Ge(lhs, rhs)
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
                return Mod(lhs, rhs)
            elif e.op == '/':
                return Div(lhs, rhs)
            else:
               raise TypeError(f"Unsupported binop: {e.op}")
        elif isinstance(e, c_ast.ID):
            return Var(ssa.use(e.name))
        elif isinstance(e, c_ast.Constant):
            return Constant(e.value)
        elif isinstance(e, c_ast.UnaryOp):
            if e.op == '-':
                hs = CParser.handle_expr(e.expr, ssa, cover)
                return Neg(hs)
            else:
               raise TypeError(f"Unsupported UnaryOp: {e.op}")
        else:
            raise TypeError(f"Unsupported expr: {e}")

    def handle_call(c, ssa):
        name = c.name.name
        if name == "assert":
            args = c.args.exprs
            assert(len(args) == 1)
            expr = CParser.handle_expr(args[0], ssa)
            return Assert(expr, c.coord.line)
        else:
            raise TypeError(f"Unsupported call: {c}")

    def handle_string_expr(expr, ssa):
        # TODO: Create a single parser to use
        parser = c_parser.CParser()
        ifexpr = "void foo() { if ("  + expr + ") {} }"
        ast = parser.parse(ifexpr)
        cond = ast.ext[0].body.block_items[0].cond
        return CParser.handle_expr(cond, ssa)

    def handle_assume(s, ssa):
        expr = s.init.value[1:-1]
        cond = CParser.handle_string_expr(expr, ssa)
        return Assume(cond, s.coord.line)

    def handle_assert(s, ssa):
        expr = s.init.value[1:-1]
        cond = CParser.handle_string_expr(expr, ssa)
        return Assert(cond, s.coord.line)



    # Returns list of stmts due to compound
    def handle_stmt(s, ssa):
        if isinstance(s, c_ast.FuncCall):
            return [CParser.handle_call(s, ssa)]
        elif isinstance(s, c_ast.Return):
            return [Return(CParser.handle_expr(s.expr, ssa), s.coord.line)]
        elif isinstance(s, c_ast.If):
            cond = CParser.handle_expr(s.cond, ssa, True)
           
            # We save the current SSA using state before branching
            ssa_current_before = ssa.copy_current()
            ssa.reset_writes()
            iffalse = CParser.handle_stmt(s.iffalse, ssa)
            false_writes = ssa.writes.copy()
             
            # Now ssa might have increased both current and next
            # we need to restore uses before handling iftrue
            # We must save the current to use it for PHI nodes
           
            ssa_false_current = ssa.copy_current() 
            
            ssa.current = ssa_current_before.copy()
            ssa.reset_writes()
            iftrue = CParser.handle_stmt(s.iftrue, ssa)
            true_writes = ssa.writes.copy()
            ssa_true_current = ssa.copy_current()
        
            ssa.current = ssa_current_before.copy()
           
            result = CParser.handle_if(s.coord.line, cond, iftrue, iffalse, ssa, ssa_current_before, ssa_false_current, ssa_true_current, false_writes, true_writes)
           
            return result
        elif isinstance(s, c_ast.Compound):
            if not s.block_items:
                return []

            items = []
            for s in s.block_items:
                items = items + CParser.handle_stmt(s, ssa)
            return items
        elif isinstance(s, c_ast.Decl):
            name = s.name
            dectype = s.type.type.names[0]
            if dectype == '__ASSUME':
                return [CParser.handle_assume(s, ssa)]
            elif dectype == '__ASSERT':
                return [CParser.handle_assert(s, ssa)]
            else:
                assert(dectype == 'int')
                if isinstance(s.init, c_ast.FuncCall):
                    assert(s.init.name.name == 'nondet_int')
                    return [Declaration(ssa.new(name), None, s.coord.line)]
                else:
                    if s.init:
                        return [Declaration(ssa.add(name), s.init.value, s.coord.line)]
                    else:
                        return [Declaration(ssa.add(name), None, s.coord.line)]
        elif isinstance(s, c_ast.Assignment):
            op = s.op
            assert(op == '=')
            rhs = CParser.handle_expr(s.rvalue, ssa)
            assert(isinstance(s.lvalue, c_ast.ID))
            lhs = Var(ssa.inc(s.lvalue.name))

            return [Assignment(lhs, rhs, s.coord.line)]
        elif isinstance(s, c_ast.For):
            raise NotImplementedError("For loops are not supported yet, please unroll them manually")
        else:
            return [Skip()]
            raise TypeError(f"Unsupported statement: {s}")

    def handle_fundef(node, ssa):
        name = node.decl.name
        args = []
        if node.decl.type.args:
            for a in node.decl.type.args.params:
                n, t = a.name, a.type.type.names[0]
                assert(t == 'int')
                args.append((ssa.new(n), t))

        stmts = []
        for s in node.body:
            ret = CParser.handle_stmt(s, ssa)
            stmts = stmts + ret

        return Function(name, args, stmts)

    def handle_node(node, ssa):
        if isinstance(node, c_ast.FuncDef):
            return CParser.handle_fundef(node, ssa)
        elif isinstance(node, c_ast.Typedef):
            #TODO: if we do not care about types this can be ignored
            return None
        elif isinstance(node, c_ast.Decl):
            #TODO: if we do not care about types this can be ignored
            return None
        else:
            print("Unsupported node", node)
            assert(False)


    def ast_to_goto(ast):
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
