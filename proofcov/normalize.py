#!/usr/bin/env python3
# Front-end normalization: rewrite a (pycparser) C program into the Assert-C subset,
# i.e., a single main function with int declarations, assignments, if-statements and
# a final assert. This automates the manual refactoring used for tcas in the paper:
#
# - typedefs of int (e.g. typedef int bool;) are treated as int
# - global variables become declarations at the start of main, initialized to 0 as in C
#   (on line NO_LINE, so the initialization is not a line of the program)
# - arrays of constant size become one variable per element (A[2] -> A__2); reading
#   with a variable index becomes an if-chain over the elements
# - calls to functions without parameters are inlined, with the local variables renamed
#   per call (f__1__x). A call inside an expression is evaluated before the statement,
#   which requires that the function has no side effects when it is conditionally
#   evaluated (right side of && and ||, branches of ?:)
# - c ? a : b becomes an if-statement assigning a fresh variable
# - assigning a truth value to an int (x = a && b;) becomes
#   if (a && b) { x = 1; } else { x = 0; }
# - a final return in main is dropped
#
# All generated statements keep the line number of the C code they come from, so
# coverage is reported on the lines of the original program. The two assignments
# generated from a truth value (and the two branches of ?:) are tagged as the
# "true" and "false" outcome of their line, see Normalizer.tags.

from pycparser import c_ast
from pycparser.c_parser import Coord
import weakref

# Line number of generated statements which are not a line of the program (e.g. the zero
# initialization of global variables); they are not counted in coverage
NO_LINE = 0


class UnsupportedError(Exception):
    pass


BOOL_OPS = {'==', '!=', '<', '>', '<=', '>=', '&&', '||'}


def is_boolean(e):
    return (isinstance(e, c_ast.BinaryOp) and e.op in BOOL_OPS) or (isinstance(e, c_ast.UnaryOp) and e.op == '!')


def int_type(name, coord):
    return c_ast.TypeDecl(name, [], None, c_ast.IdentifierType(['int'], coord), coord)


def make_decl(name, init, coord):
    return c_ast.Decl(name, [], None, [], [], int_type(name, coord), init, None, coord)


def make_assign(name, rvalue, coord):
    return c_ast.Assignment('=', c_ast.ID(name, coord), rvalue, coord)


def make_const(value, coord):
    return c_ast.Constant('int', str(value), coord)


def as_block(stmts, coord):
    return c_ast.Compound(stmts if stmts else None, coord)


def is_constant(e):
    return isinstance(e, c_ast.Constant) or (isinstance(e, c_ast.UnaryOp) and e.op == '-' and isinstance(e.expr, c_ast.Constant))


def constant_value(e):
    if isinstance(e, c_ast.Constant):
        return int(e.value, 0)
    return -int(e.expr.value, 0)


class Normalizer():
    def __init__(self, ast):
        self.typedefs = set()
        self.functions = {}
        self.global_decls = []
        # Arrays (normalized name -> size)
        self.arrays = {}
        # Scopes map C names to normalized names, innermost last
        self.scopes = [{}]
        self.inline_stack = []
        self.counter = 0
        self.purity = {}
        # Generated assignment -> "true"/"false" outcome of its line
        self.tags = weakref.WeakKeyDictionary()

        for node in ast.ext:
            if isinstance(node, c_ast.Typedef):
                self.check_int_type(node.type, node.coord)
                self.typedefs.add(node.name)
            elif isinstance(node, c_ast.FuncDef):
                self.functions[node.decl.name] = node
            elif isinstance(node, c_ast.Decl):
                if isinstance(node.type, c_ast.FuncDecl):
                    continue  # function prototype
                self.global_decls.append(node)
            else:
                raise UnsupportedError(f"Unsupported top-level node at line {node.coord.line}: {type(node).__name__}")

        if 'main' not in self.functions:
            raise UnsupportedError("No main function")

    def check_int_type(self, t, coord):
        if not (isinstance(t, c_ast.TypeDecl) and isinstance(t.type, c_ast.IdentifierType)):
            raise UnsupportedError(f"Unsupported type at line {coord.line}")
        names = t.type.names
        if names != ['int'] and not (len(names) == 1 and names[0] in self.typedefs):
            raise UnsupportedError(f"Unsupported type {' '.join(names)} at line {coord.line}")

    def fresh(self, base):
        self.counter += 1
        return f"{base}__{self.counter}"

    def lookup(self, name, coord):
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        raise UnsupportedError(f"Unknown variable {name} at line {coord.line}")

    # Returns the normalized program (a FileAST with only main) and the outcome tags
    def normalize(self):
        main = self.functions['main']
        stmts = []
        for d in self.global_decls:
            stmts += self.declare(d, d.name, self.scopes[0], zero_init=True)

        # Locals of main keep their names
        scope = {}
        for name in self.local_names(main):
            if name in self.scopes[0]:
                raise UnsupportedError(f"Local variable {name} in main shadows a global variable")
            scope[name] = name
        self.scopes.append(scope)
        items = list(main.body.block_items or [])
        if items and isinstance(items[-1], c_ast.Return):
            items = items[:-1]  # nothing is executed after a final return in main
        self.check_no_return(items, 'main')
        for s in items:
            stmts += self.stmt(s)
        self.scopes.pop()

        coord = main.coord
        functype = c_ast.FuncDecl(None, c_ast.TypeDecl('main', [], None, c_ast.IdentifierType(['void'], coord), coord), coord)
        decl = c_ast.Decl('main', [], None, [], [], functype, None, None, coord)
        fundef = c_ast.FuncDef(decl, None, c_ast.Compound(stmts, main.body.coord), coord)
        return c_ast.FileAST([fundef]), self.tags

    # Names of all variables declared in a function body (they must be unique in the function)
    def local_names(self, fundef):
        names = []

        class Visitor(c_ast.NodeVisitor):
            def visit_Decl(self, node):
                names.append(node.name)
                self.generic_visit(node)

        Visitor().visit(fundef.body)
        duplicates = {n for n in names if names.count(n) > 1}
        if duplicates:
            raise UnsupportedError(f"Variables declared more than once in {fundef.decl.name}: {', '.join(sorted(duplicates))}")
        return names

    def check_no_return(self, items, fname):
        class Visitor(c_ast.NodeVisitor):
            def visit_Return(self, node):
                raise UnsupportedError(f"Unsupported: return before the end of {fname} at line {node.coord.line}")

        for s in items:
            Visitor().visit(s)

    # Declare a variable (scalar or array) under a normalized name in scope. With zero_init
    # (global variables) a declaration without a value is initialized to 0, as in C.
    def declare(self, d, new_name, scope, zero_init=False):
        no_line = Coord(d.coord.file, NO_LINE)
        if isinstance(d.type, c_ast.ArrayDecl):
            self.check_int_type(d.type.type, d.coord)
            if d.init is not None or not isinstance(d.type.dim, c_ast.Constant):
                raise UnsupportedError(f"Unsupported array declaration at line {d.coord.line}")
            size = int(d.type.dim.value, 0)
            scope[d.name] = new_name
            self.arrays[new_name] = size
            if zero_init:
                return [make_decl(f"{new_name}__{i}", make_const(0, no_line), no_line) for i in range(size)]
            return [make_decl(f"{new_name}__{i}", None, d.coord) for i in range(size)]

        self.check_int_type(d.type, d.coord)
        scope[d.name] = new_name
        init = d.init
        if init is None and zero_init:
            return [make_decl(new_name, make_const(0, no_line), no_line)]
        if init is None or is_constant(init) or (isinstance(init, c_ast.FuncCall) and init.name.name == 'nondet_int'):
            return [make_decl(new_name, init, d.coord)]
        # int x = <expression>; becomes a declaration and an assignment on the same line
        pre, e = self.expr(init)
        return [make_decl(new_name, None, d.coord)] + pre + self.assign(new_name, e, d.coord)

    # Assign e to a variable, a truth value becomes an if-statement
    def assign(self, name, e, coord):
        if is_boolean(e):
            assign_true = make_assign(name, make_const(1, coord), coord)
            assign_false = make_assign(name, make_const(0, coord), coord)
            self.tags[assign_true] = "true"
            self.tags[assign_false] = "false"
            return [c_ast.If(e, as_block([assign_true], coord), as_block([assign_false], coord), coord)]
        return [make_assign(name, e, coord)]

    def lvalue_name(self, lv):
        if isinstance(lv, c_ast.ID):
            name = self.lookup(lv.name, lv.coord)
            if name in self.arrays:
                raise UnsupportedError(f"Unsupported: assigning an array at line {lv.coord.line}")
            return name
        if isinstance(lv, c_ast.ArrayRef) and isinstance(lv.name, c_ast.ID):
            name = self.lookup(lv.name.name, lv.coord)
            if name in self.arrays and is_constant(lv.subscript):
                index = constant_value(lv.subscript)
                if 0 <= index < self.arrays[name]:
                    return f"{name}__{index}"
        raise UnsupportedError(f"Unsupported assignment target at line {lv.coord.line}")

    # Normalize a statement into a list of statements
    def stmt(self, s):
        if isinstance(s, c_ast.Compound):
            stmts = []
            for item in s.block_items or []:
                stmts += self.stmt(item)
            return [as_block(stmts, s.coord)]
        elif isinstance(s, c_ast.Decl):
            # The (renamed) name of a local variable is already in the innermost scope
            return self.declare(s, self.lookup(s.name, s.coord), self.scopes[-1])
        elif isinstance(s, c_ast.Assignment):
            if s.op != '=':
                raise UnsupportedError(f"Unsupported assignment operator {s.op} at line {s.coord.line}")
            name = self.lvalue_name(s.lvalue)
            pre, e = self.expr(s.rvalue)
            return pre + self.assign(name, e, s.coord)
        elif isinstance(s, c_ast.If):
            pre, cond = self.expr(s.cond)
            iftrue = as_block(self.stmt(s.iftrue), s.iftrue.coord)
            iffalse = as_block(self.stmt(s.iffalse), s.iffalse.coord) if s.iffalse is not None else None
            return pre + [c_ast.If(cond, iftrue, iffalse, s.coord)]
        elif isinstance(s, c_ast.FuncCall):
            name = s.name.name
            if name == 'assert':
                args = s.args.exprs if s.args else []
                if len(args) != 1:
                    raise UnsupportedError(f"assert takes one argument at line {s.coord.line}")
                pre, e = self.expr(args[0])
                return pre + [c_ast.FuncCall(c_ast.ID('assert', s.coord), c_ast.ExprList([e], s.coord), s.coord)]
            pre, _ = self.inline(s, conditional=False, value_needed=False)
            return pre
        elif isinstance(s, c_ast.EmptyStatement):
            return []
        else:
            raise UnsupportedError(f"Unsupported statement at line {s.coord.line}: {type(s).__name__}")

    # Normalize an expression. Returns statements to execute before it and the new expression.
    # conditional is True when C might not evaluate the expression (short-circuit, ?:)
    def expr(self, e, conditional=False):
        if isinstance(e, c_ast.ID):
            name = self.lookup(e.name, e.coord)
            if name in self.arrays:
                raise UnsupportedError(f"Unsupported: array {e.name} used as a value at line {e.coord.line}")
            return [], c_ast.ID(name, e.coord)
        elif isinstance(e, c_ast.Constant):
            if e.type != 'int':
                raise UnsupportedError(f"Unsupported constant {e.value} at line {e.coord.line}")
            return [], c_ast.Constant('int', e.value, e.coord)
        elif isinstance(e, c_ast.BinaryOp):
            pre_l, lhs = self.expr(e.left, conditional)
            pre_r, rhs = self.expr(e.right, conditional or e.op in ('&&', '||'))
            return pre_l + pre_r, c_ast.BinaryOp(e.op, lhs, rhs, e.coord)
        elif isinstance(e, c_ast.UnaryOp):
            if e.op not in ('-', '!', '+'):
                raise UnsupportedError(f"Unsupported operator {e.op} at line {e.coord.line}")
            pre, hs = self.expr(e.expr, conditional)
            if e.op == '+':
                return pre, hs
            return pre, c_ast.UnaryOp(e.op, hs, e.coord)
        elif isinstance(e, c_ast.TernaryOp):
            pre_c, cond = self.expr(e.cond, conditional)
            pre_t, e_true = self.expr(e.iftrue, True)
            pre_f, e_false = self.expr(e.iffalse, True)
            temp = self.fresh("ternary")
            assign_true = self.assign(temp, e_true, e.coord)
            assign_false = self.assign(temp, e_false, e.coord)
            # The two branches are the outcomes of the line (unless they are truth values themselves)
            if isinstance(assign_true[0], c_ast.Assignment) and isinstance(assign_false[0], c_ast.Assignment):
                self.tags[assign_true[0]] = "true"
                self.tags[assign_false[0]] = "false"
            branches = c_ast.If(cond, as_block(pre_t + assign_true, e.coord), as_block(pre_f + assign_false, e.coord), e.coord)
            return pre_c + [make_decl(temp, None, e.coord), branches], c_ast.ID(temp, e.coord)
        elif isinstance(e, c_ast.ArrayRef):
            if not isinstance(e.name, c_ast.ID):
                raise UnsupportedError(f"Unsupported array access at line {e.coord.line}")
            name = self.lookup(e.name.name, e.coord)
            if name not in self.arrays:
                raise UnsupportedError(f"{e.name.name} is not an array at line {e.coord.line}")
            size = self.arrays[name]
            pre, index = self.expr(e.subscript, conditional)
            if is_constant(index):
                i = constant_value(index)
                if not 0 <= i < size:
                    raise UnsupportedError(f"Array index out of bounds at line {e.coord.line}")
                return pre, c_ast.ID(f"{name}__{i}", e.coord)
            # A variable index becomes: if (i == 0) t = A__0; else if (i == 1) t = A__1; ...
            # Outside the bounds t has no value (out of bounds reads are undefined in C)
            temp = self.fresh(f"{name}__read")
            chain = None
            for i in reversed(range(size)):
                test = c_ast.BinaryOp('==', index, make_const(i, e.coord), e.coord)
                read = as_block([make_assign(temp, c_ast.ID(f"{name}__{i}", e.coord), e.coord)], e.coord)
                chain = c_ast.If(test, read, as_block([chain], e.coord) if chain else None, e.coord)
            return pre + [make_decl(temp, None, e.coord), chain], c_ast.ID(temp, e.coord)
        elif isinstance(e, c_ast.FuncCall):
            return self.inline(e, conditional, value_needed=True)
        else:
            raise UnsupportedError(f"Unsupported expression at line {e.coord.line}: {type(e).__name__}")

    # A function has side effects if it assigns a variable which is not its own, or calls such a function
    def has_side_effects(self, fname):
        if fname not in self.purity:
            self.purity[fname] = True  # assume side effects while checking (recursion is rejected anyway)
            f = self.functions[fname]
            local = set(self.local_names(f))
            normalizer = self
            effects = []

            class Visitor(c_ast.NodeVisitor):
                def visit_Assignment(self, node):
                    lv = node.lvalue.name if isinstance(node.lvalue, c_ast.ArrayRef) else node.lvalue
                    if not (isinstance(lv, c_ast.ID) and lv.name in local):
                        effects.append(node)
                    self.generic_visit(node)

                def visit_FuncCall(self, node):
                    name = node.name.name
                    if name in normalizer.functions and normalizer.has_side_effects(name):
                        effects.append(node)
                    self.generic_visit(node)

            Visitor().visit(f.body)
            self.purity[fname] = bool(effects)
        return self.purity[fname]

    # Inline a call to a function without parameters. Returns the statements of the
    # function body and the variable holding the returned value (None for void functions)
    def inline(self, call, conditional, value_needed):
        fname = call.name.name
        if fname not in self.functions:
            raise UnsupportedError(f"Unsupported call to {fname} at line {call.coord.line}")
        if fname in self.inline_stack:
            raise UnsupportedError(f"Unsupported: recursive call to {fname} at line {call.coord.line}")
        if call.args is not None and call.args.exprs:
            raise UnsupportedError(f"Unsupported: call with arguments to {fname} at line {call.coord.line}")
        if conditional and self.has_side_effects(fname):
            raise UnsupportedError(f"Unsupported: conditionally evaluated call to {fname} with side effects at line {call.coord.line}")

        f = self.functions[fname]
        params = f.decl.type.args
        if params is not None and not (len(params.params) == 1 and isinstance(params.params[0], c_ast.Typename)):
            raise UnsupportedError(f"Unsupported: function {fname} with parameters")

        self.counter += 1
        prefix = f"{fname}__{self.counter}__"
        self.scopes.append({name: prefix + name for name in self.local_names(f)})
        self.inline_stack.append(fname)

        items = list(f.body.block_items or [])
        ret = None
        if items and isinstance(items[-1], c_ast.Return):
            ret = items[-1]
            items = items[:-1]
        self.check_no_return(items, fname)

        stmts = []
        for s in items:
            stmts += self.stmt(s)

        ret_var = None
        if ret is not None and ret.expr is not None:
            ret_var = prefix + "return"
            pre, e = self.expr(ret.expr)
            stmts += [make_decl(ret_var, None, ret.coord)] + pre + self.assign(ret_var, e, ret.coord)
        elif value_needed:
            raise UnsupportedError(f"Unsupported: {fname} does not end with a return at line {call.coord.line}")

        self.inline_stack.pop()
        self.scopes.pop()
        return stmts, (c_ast.ID(ret_var, call.coord) if ret_var else None)


def normalize(ast):
    return Normalizer(ast).normalize()
