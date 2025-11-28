#!/usr/bin/env python3

#### GOTO Expressions

class Expr():
    def __init__(self):
        None

class UnaryOp(Expr):
    def __init__(self, hs):
        self.hs = hs
        
    def get_variables(self):
        return self.hs.get_variables()

class Neg(UnaryOp):
    def to_ssa(self, uses):
        return Neg(self.hs.to_ssa(uses))

    def to_bmc(self, track_undef):
         return "(- 0 " + self.hs.to_bmc(track_undef) + ")" # TODO: Fix unary - SMT

   
    def __str__(self):
        return "-" + str(self.hs)

class Not(UnaryOp):
    def to_ssa(self, uses):
        return Not(self.hs.to_ssa(uses))

    def to_bmc(self, track_undef):
         return "(not " + self.hs.to_bmc(track_undef) + ")"

    def __str__(self):
        return "!" + str(self.hs)


class BinOp(Expr):
    def __init__(self, lhs, rhs):
        self.lhs = lhs
        self.rhs = rhs
        
    def get_variables(self):
        return self.lhs.get_variables() + self.rhs.get_variables()

class Eq(BinOp):
    op = '=='
    def to_ssa(self, uses):
        return Eq(self.lhs.to_ssa(uses), self.rhs.to_ssa(uses))

    def to_bmc(self, track_undef):
        return "(= " + self.lhs.to_bmc(track_undef) + " " + self.rhs.to_bmc(track_undef) + ")"

    def __str__(self):
        return str(self.lhs) + " == " + str(self.rhs)

class Ne(BinOp):
    op = '!='
    def to_ssa(self, uses):
        return Ne(self.lhs.to_ssa(uses), self.rhs.to_ssa(uses))

    def to_bmc(self, track_undef):
        return "(not (= " + self.lhs.to_bmc(track_undef) + " " + self.rhs.to_bmc(track_undef) + "))"

    def __str__(self):
        return str(self.lhs) + " != " + str(self.rhs)



class Gt(BinOp):
    op = '>'

    def to_ssa(self, uses):
        return Gt(self.lhs.to_ssa(uses), self.rhs.to_ssa(uses))

    def to_bmc(self, track_undef):
        return "(> " + self.lhs.to_bmc(track_undef) + " " + self.rhs.to_bmc(track_undef) + ")"

    def __str__(self):
        return str(self.lhs) + " > " + str(self.rhs)

class Ge(BinOp):
    op = '>='

    def to_ssa(self, uses):
        return Ge(self.lhs.to_ssa(uses), self.rhs.to_ssa(uses))

    def to_bmc(self, track_undef):
        return "(>= " + self.lhs.to_bmc(track_undef) + " " + self.rhs.to_bmc(track_undef) + ")"

    def __str__(self):
        return str(self.lhs) + " >= " + str(self.rhs)

class Lt(BinOp):
    op = '<'

    def to_ssa(self, uses):
        return Lt(self.lhs.to_ssa(uses), self.rhs.to_ssa(uses))

    def to_bmc(self, track_undef):
        return "(< " + self.lhs.to_bmc(track_undef) + " " + self.rhs.to_bmc(track_undef) + ")"

    def __str__(self):
        return str(self.lhs) + " < " + str(self.rhs)


class Le(BinOp):
    def to_ssa(self, uses):
        return Le(self.lhs.to_ssa(uses), self.rhs.to_ssa(uses))

    def to_bmc(self, track_undef):
        return "(<= " + self.lhs.to_bmc(track_undef) + " " + self.rhs.to_bmc(track_undef) + ")"

    def __str__(self):
        return str(self.lhs) + " <= " + str(self.rhs)

class Div(BinOp):
    def to_ssa(self, uses):
        return Div(self.lhs.to_ssa(uses), self.rhs.to_ssa(uses))

    def to_bmc(self, track_undef):
        return "(div " + self.lhs.to_bmc(track_undef) + " " + self.rhs.to_bmc(track_undef) + ")"

    def __str__(self):
        return str(self.lhs) + " / " + str(self.rhs)

class Mod(BinOp):
    def to_ssa(self, uses):
        return Mod(self.lhs.to_ssa(uses), self.rhs.to_ssa(uses))

    def to_bmc(self, track_undef):
        return "(mod " + self.lhs.to_bmc(track_undef) + " " + self.rhs.to_bmc(track_undef) + ")"

    def __str__(self):
        return str(self.lhs) + " % " + str(self.rhs)

# Boolean

class And(BinOp):
    op = '&&'
    def to_ssa(self, uses):
        return And(self.lhs.to_ssa(uses), self.rhs.to_ssa(uses))

    def to_bmc(self, track_undef):
        return "(and " + self.lhs.to_bmc(track_undef) + " " + self.rhs.to_bmc(track_undef) + ")"

    def __str__(self):
        return str(self.lhs) + " && " + str(self.rhs)

class Or(BinOp):
    op = '||'
    def to_ssa(self, uses):
        return Or(self.lhs.to_ssa(uses), self.rhs.to_ssa(uses))

    def to_bmc(self, track_undef):
        return "(or " + self.lhs.to_bmc(track_undef) + " " + self.rhs.to_bmc(track_undef) + ")"

    def __str__(self):
        return str(self.lhs) + " || " + str(self.rhs)




# Integer

class Add(BinOp):
    def to_ssa(self, uses):
        return Add(self.lhs.to_ssa(uses), self.rhs.to_ssa(uses))

    def to_bmc(self, track_undef):
        return "(+ " + self.lhs.to_bmc(track_undef) + " " + self.rhs.to_bmc(track_undef) + ")"

    def __str__(self):
        return str(self.lhs) + " + " + str(self.rhs)

class Sub(BinOp):
    def to_ssa(self, uses):
        return Sub(self.lhs.to_ssa(uses), self.rhs.to_ssa(uses))

    def to_bmc(self, track_undef):
        return "(- " + self.lhs.to_bmc(track_undef) + " " + self.rhs.to_bmc(track_undef) + ")"

    def __str__(self):
        return str(self.lhs) + " - " + str(self.rhs)



class Mul(BinOp):
    def to_ssa(self, uses):
        return Mul(self.lhs.to_ssa(uses), self.rhs.to_ssa(uses))

    def to_bmc(self, track_undef):
        return "(* " + self.lhs.to_bmc(track_undef) + " " + self.rhs.to_bmc(track_undef) + ")"

    def __str__(self):
        return str(self.lhs) + " * " + str(self.rhs)




class Var(Expr):
    def __init__(self, name):
        self.name = name

    def to_bmc(self, track_undef):
        return self.name

    def get_variables(self):
        return [self.name]
    
    def __str__(self):
        return self.name

class Constant(Expr):
    def __init__(self, val):
        self.val = val

    def to_bmc(self, track_undef):
        return str(self.val)

    def get_variables(self):
        return []
    
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
        
    def to_bmc(self, track_undef):
        return []
    
    def __str__(self):
        return "SKIP"
    

class Assert(Line):
    def __init__(self, expr, src_line):
        self.expr = expr
        self.src_line = src_line

    def to_bmc(self, track_undef):
        # TODO: what about asserts?
        return ["(not " + self.expr.to_bmc(track_undef) + ")"]

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

    def to_bmc(self, track_undef):
        # TODO: check
        if track_undef:
            return ["(and (= " + self.name + " " + self.value + ") (= " + self.name + ".undef 0))"]
        else:
            return ["(and (= " + self.name + " " + self.value + "))"]

    
class Assignment(Line):
    def __init__(self, lhs, rhs, src_line):
        self.lhs = lhs
        assert(not isinstance(lhs, str))
        self.rhs = rhs
        self.src_line = src_line

    def assignment(self):
        return self.lhs

    def to_bmc(self, track_undef):
        # TODO: check  
        if track_undef:
            return ["(and (= " + self.lhs.to_bmc(track_undef) + " " + self.rhs.to_bmc(track_undef) + ") (= " + self.lhs.to_bmc(track_undef) + ".undef 0))"]
        else:
            return ["(and (= " + self.lhs.to_bmc(track_undef) + " " + self.rhs.to_bmc(track_undef) + "))"]

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



    def to_bmc(self, track_undef):
        if track_undef:
            variables = self.cond.get_variables()
            print(f'\n\nVariables in phi condition: {variables}')
            
            if variables == []:
                # We can not skip the phi if there are no variables in the condition
                undef_cond = []  # False
            else:
            # If we have one undef variable, the phi can be skipped, including the assigned one
                undef_cond =  list(map(lambda v : f"(= {v}.undef 1)", variables))
            undef_cond_true = "(or " + " ".join(undef_cond) + " (= " + self.iftrue + ".undef 1))"
            undef_cond_false = "(or " + " ".join(undef_cond) + " (= " + self.iffalse + ".undef 1))"
            
            # We introduce two variables, one which restricts the true branch, one for the false branch
            true_var = "phi.if." + str(self.src_line) + "." + self.var + ".true"
            false_var = "phi.else." + str(self.src_line) + "." + self.var + ".false"
        
            decl_true = "(declare-fun " + true_var + " () (Int))" 
            decl_false = "(declare-fun " + false_var + " () (Int))"
        
            # Either true_var holds or undef cond holds 
            true_cond = "(or (= " + true_var + " 1) " + undef_cond_true + ")"
            false_cond = "(or (= " + false_var + " 1) " + undef_cond_false + ")"
        
            
            notcond = "(not " + self.cond.to_bmc(track_undef) + ")"
            ift = "(and (= " + self.var + " " + str(self.iftrue) + ") " + "(= " + self.var + ".undef 0))"
            iff = "(and (= " + self.var + " " + str(self.iffalse) + ") " + "(= " + self.var + ".undef 0))"
        
            a = "(or " + notcond + " " + ift + " (= " + true_var + " 0))"
            b = "(or " + self.cond.to_bmc(track_undef) + " " + iff + " (= " + false_var + " 0))"
            return [decl_true, true_cond, a, decl_false, false_cond, b]
        else:
            notcond = "(not " + self.cond.to_bmc(track_undef) + ")"
            ift = "(= " + self.var + " " + str(self.iftrue) + ")"
            iff = "(= " + self.var + " " + str(self.iffalse) + ")"
            a = "(or " + notcond + " " + ift + ")"
            b = "(or " + self.cond.to_bmc(track_undef) + " " + iff + ")"
            return [a, b]


    def agnostic_bmc(self, track_undef):
        return ["(or (= " + self.var + " " + str(self.iftrue) + ") (= " + self.var + " " + str(self.iffalse) + "))"]  

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
    