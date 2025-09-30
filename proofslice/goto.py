#!/usr/bin/env python3

#### GOTO Expressions

class Expr():
    def __init__(self):
        None

class UnaryOp(Expr):
    def __init__(self, hs):
        self.hs = hs

class Neg(UnaryOp):
    def to_ssa(self, uses):
        return Neg(self.hs.to_ssa(uses))

    def to_bmc(self):
         return "(- 0 " + self.hs.to_bmc() + ")" # TODO: Fix unary - SMT

    def __str__(self):
        return "-" + str(self.hs)



class BinOp(Expr):
    def __init__(self, lhs, rhs):
        self.lhs = lhs
        self.rhs = rhs

class Eq(BinOp):
    op = '=='
    def to_ssa(self, uses):
        return Eq(self.lhs.to_ssa(uses), self.rhs.to_ssa(uses))

    def to_bmc(self):
        return "(= " + self.lhs.to_bmc() + " " + self.rhs.to_bmc() + ")"

    def __str__(self):
        return str(self.lhs) + " == " + str(self.rhs)

class Ne(BinOp):
    op = '!='
    def to_ssa(self, uses):
        return Ne(self.lhs.to_ssa(uses), self.rhs.to_ssa(uses))

    def to_bmc(self):
        return "(not (= " + self.lhs.to_bmc() + " " + self.rhs.to_bmc() + "))"

    def __str__(self):
        return str(self.lhs) + " != " + str(self.rhs)



class Gt(BinOp):
    op = '>'

    def to_ssa(self, uses):
        return Gt(self.lhs.to_ssa(uses), self.rhs.to_ssa(uses))

    def to_bmc(self):
        return "(> " + self.lhs.to_bmc() + " " + self.rhs.to_bmc() + ")"

    def __str__(self):
        return str(self.lhs) + " > " + str(self.rhs)

class Ge(BinOp):
    op = '>='

    def to_ssa(self, uses):
        return Ge(self.lhs.to_ssa(uses), self.rhs.to_ssa(uses))

    def to_bmc(self):
        return "(>= " + self.lhs.to_bmc() + " " + self.rhs.to_bmc() + ")"

    def __str__(self):
        return str(self.lhs) + " >= " + str(self.rhs)

class Le(BinOp):
    def to_ssa(self, uses):
        return Le(self.lhs.to_ssa(uses), self.rhs.to_ssa(uses))

    def to_bmc(self):
        return "(<= " + self.lhs.to_bmc() + " " + self.rhs.to_bmc() + ")"

    def __str__(self):
        return str(self.lhs) + " <= " + str(self.rhs)

class Div(BinOp):
    def to_ssa(self, uses):
        return Div(self.lhs.to_ssa(uses), self.rhs.to_ssa(uses))

    def to_bmc(self):
        return "(div " + self.lhs.to_bmc() + " " + self.rhs.to_bmc() + ")"

    def __str__(self):
        return str(self.lhs) + " / " + str(self.rhs)

class Mod(BinOp):
    def to_ssa(self, uses):
        return Mod(self.lhs.to_ssa(uses), self.rhs.to_ssa(uses))

    def to_bmc(self):
        return "(mod " + self.lhs.to_bmc() + " " + self.rhs.to_bmc() + ")"

    def __str__(self):
        return str(self.lhs) + " % " + str(self.rhs)

# Boolean

class And(BinOp):
    op = '&&'
    def to_ssa(self, uses):
        return And(self.lhs.to_ssa(uses), self.rhs.to_ssa(uses))

    def to_bmc(self):
        return "(and " + self.lhs.to_bmc() + " " + self.rhs.to_bmc() + ")"

    def __str__(self):
        return str(self.lhs) + " && " + str(self.rhs)

class Or(BinOp):
    op = '||'
    def to_ssa(self, uses):
        return Or(self.lhs.to_ssa(uses), self.rhs.to_ssa(uses))

    def to_bmc(self):
        return "(or " + self.lhs.to_bmc() + " " + self.rhs.to_bmc() + ")"

    def __str__(self):
        return str(self.lhs) + " || " + str(self.rhs)




# Integer

class Add(BinOp):
    def to_ssa(self, uses):
        return Add(self.lhs.to_ssa(uses), self.rhs.to_ssa(uses))

    def to_bmc(self):
        return "(+ " + self.lhs.to_bmc() + " " + self.rhs.to_bmc() + ")"

    def __str__(self):
        return str(self.lhs) + " + " + str(self.rhs)

class Sub(BinOp):
    def to_ssa(self, uses):
        return Sub(self.lhs.to_ssa(uses), self.rhs.to_ssa(uses))

    def to_bmc(self):
        return "(- " + self.lhs.to_bmc() + " " + self.rhs.to_bmc() + ")"

    def __str__(self):
        return str(self.lhs) + " - " + str(self.rhs)



class Mul(BinOp):
    def to_ssa(self, uses):
        return Mul(self.lhs.to_ssa(uses), self.rhs.to_ssa(uses))

    def to_bmc(self):
        return "(* " + self.lhs.to_bmc() + " " + self.rhs.to_bmc() + ")"

    def __str__(self):
        return str(self.lhs) + " * " + str(self.rhs)




class Var(Expr):
    def __init__(self, name):
        self.name = name

    def to_bmc(self):
        return self.name

    def __str__(self):
        return self.name

class Constant(Expr):
    def __init__(self, val):
        self.val = val

    def to_bmc(self):
        return str(self.val)

    def __str__(self):
        return str(self.val)

#### GOTO Programs

class Line():
    def assignment(self):
        None

    def __init__(self, src_line=None):
        None

class Skip(Line):
    def __init__(self):
        None
        
    def to_bmc(self):
        return []
    
    def __str__(self):
        return "SKIP"
    
class Assume(Line):
    def __init__(self, expr, src_line):
        self.expr = expr
        self.src_line = src_line

    def to_bmc(self):
        return [self.expr.to_bmc()]

    def __str__(self):
        return "ASSUME(" + str(self.expr) + ")"



class Assert(Line):
    def __init__(self, expr, src_line):
        self.expr = expr
        self.src_line = src_line

    def to_bmc(self):
        return ["(not " + self.expr.to_bmc() + ")"]

    def __str__(self):
        return "ASSERT(" + str(self.expr) + ")"

class Return(Line):
    def __init__(self, expr, src_line):
        self.expr = expr
        self.src_line = src_line

    def __str__(self):
        return "RETURN(" + str(self.expr) + ")"

class Declaration(Line):
    def __init__(self, name, value, src_line):
        self.name = name
        self.value = value
        self.src_line = src_line

    def __str__(self):
        return "DECL(" + str(self.name) + ", " + str(self.value) + ")"

    def to_bmc(self):
        return ["(= " + self.name + " " + self.value + ")"]
        assert(False)

    
class Assignment(Line):
    def __init__(self, lhs, rhs, src_line):
        self.lhs = lhs
        assert(not isinstance(lhs, str))
        self.rhs = rhs
        self.src_line = src_line

    def assignment(self):
        return self.lhs

    def to_bmc(self):
        return ["(= " + self.lhs.to_bmc() + " " + self.rhs.to_bmc() + ")"]

    def __str__(self):
        return str(self.lhs) + " := " + str(self.rhs)



class Jump(Line):
    def __init__(self, target, src_line):
        self.target = target
        self.src_line = src_line

    def __str__(self):
        return "JUMP(" + str(self.target) + ")"



class JumpIf(Line):
    def __init__(self, cond, target, src_line):
        self.cond = cond
        self.target = target
        self.src_line = src_line

    def to_ssa(self, uses):
        return JumpIf(self.cond.to_ssa(uses), self.target)

    def __str__(self):
        return "JUMPIF(" + str(self.cond) + ", " + str(self.target) + ")"

class Label(Line):
    def __init__(self, label, src_line):
        self.label = label
        self.src_line = src_line

    def __str__(self):
        return self.label+ ":"

# Merging two values depending on control flow
class Phi(Line):
    def __init__(self, var, cond, iftrue, iffalse, src_line):
        self.var = var
        self.cond = cond
        self.iftrue = iftrue
        self.iffalse = iffalse
        self.src_line = src_line

    def to_bmc(self):
        notcond = "(not " + self.cond.to_bmc() + ")"
        ift = "(= " + self.var + " " + str(self.iftrue) + ")"
        iff = "(= " + self.var + " " + str(self.iffalse) + ")"
        a = "(or " + notcond + " " + ift + ")"
        b = "(or " + self.cond.to_bmc() + " " + iff + ")"
        return [a, b]

    def __str__(self):
        return "PHI(" + str(self.var) + ") := " + str(self.cond) + " ? " + str(self.iftrue) + " : " + str(self.iffalse)
    
class Function():
    def __init__(self, name, args, body):
        self.name = name
        self.args = args
        self.body = body

    def __str__(self):
        textargs = ', '.join(map(lambda x : x[1] + ' '  + x[0], self.args))
        textbody = '\n'.join(map(lambda x : '\t' + str(x), self.body))
        return "FUN " + self.name + "(" + textargs + "):" + "\n" + textbody

