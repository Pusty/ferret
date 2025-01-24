# https://inria.hal.science/hal-04315477/ - Gröbner Bases for Boolean Function Minimization

import pyeda
from pyeda.inter import exprvar, expr2truthtable, espresso_tts

from sympy import groebner, GF, symbols, prod, Mul, Add, Pow, Poly, Symbol, factor_list
from sympy.logic.boolalg import to_dnf, Not, And, Or, Xor, BooleanTrue, BooleanFalse, simplify_logic


def sympy_to_pyeda(expr):
    if isinstance(expr, Or):
        return pyeda.boolalg.expr.Or(*[sympy_to_pyeda(x) for x in expr.args], simplify=False)
    elif isinstance(expr, And):
        return pyeda.boolalg.expr.And(*[sympy_to_pyeda(x) for x in expr.args], simplify=False)
    elif isinstance(expr, Xor):
        return pyeda.boolalg.expr.Xor(*[sympy_to_pyeda(x) for x in expr.args], simplify=False)
    elif isinstance(expr, Not):
        return pyeda.boolalg.expr.Not(sympy_to_pyeda(expr.args[0]))
    elif isinstance(expr, Symbol):
        return exprvar(expr.name)
    elif isinstance(expr, BooleanTrue):
        return pyeda.boolalg.expr.One 
    elif isinstance(expr, BooleanFalse):
        return pyeda.boolalg.expr.Zero 
    else:
        print("sympy_to_pyeda", type(expr))

def pyeda_to_sympy(expr):
    if isinstance(expr, pyeda.boolalg.expr.OrOp):
        return Or(*[pyeda_to_sympy(x) for x in expr.xs])
    elif isinstance(expr, pyeda.boolalg.expr.AndOp):
        return And(*[pyeda_to_sympy(x) for x in expr.xs])
    elif isinstance(expr, pyeda.boolalg.expr.XorOp):
        return Xor(*[pyeda_to_sympy(x) for x in expr.xs])
    elif isinstance(expr, pyeda.boolalg.expr.Complement):
        return Not(pyeda_to_sympy(expr.__invert__()))
    elif isinstance(expr, pyeda.boolalg.expr.Variable):
        return Symbol(expr.name)
    elif isinstance(expr, pyeda.boolalg.expr._One):
        return True
    elif isinstance(expr, pyeda.boolalg.expr._Zero):
        return False
    else:
        print("pyeda_to_sympy", type(expr))
    

def espresso_to_dnf(expr):
    pyeda_expr = sympy_to_pyeda(expr)
    ttb = expr2truthtable(pyeda_expr)
    espresso = espresso_tts(ttb)[0]
    return pyeda_to_sympy(espresso)


def alg_encode(f, x):
    #f = to_dnf(f, len(x) < 8) # to DNF + Quine-McCluskey simplification (if len(x) < 8)
    f = espresso_to_dnf(f)
    # Or(And(...))
    terms = []
    aargs = f.args if isinstance(f,Or) else [f]
    for andterm in aargs:
        innerterm = []
        cargs = andterm.args if isinstance(andterm, And) else [andterm]
        for v in cargs:
            if isinstance(v, Not):
                innerterm.append(v.args[0]+1)
            else:
                if v == True: v = 1
                if v == False: v = 0
                innerterm.append(v)  
        terms.append(prod(innerterm))
    for i in range(len(x)):
        terms.append(x[i]*x[i] + x[i])
    return terms

def alg_decode_term(term):
    if isinstance(term, Add):
        return Xor(*[alg_decode_term(arg) for arg in term.args])
    elif isinstance(term, Mul):
        return And(*[alg_decode_term(arg) for arg in term.args])
    elif isinstance(term, Pow):
        n = term.args[1]
        r = alg_decode_term(term.args[0])
        return And(*[r for _ in range(n)])
    else:
        return term
            
def alg_decode(f_a, x):
    return simplify_logic(Or(*[alg_decode_term(term) for term in f_a]))
    

def minimize(formula, x, depthLeft=5, negate=False):
    ideal = alg_encode(formula, x)
    G = groebner(ideal, x, domain=GF(2), order='lex')
    output = []
    for g in G.args[0]:

        # Ignore trivial elements
        trivial = False
        for i in range(len(x)):
            trivial = trivial or (g == x[i]*x[i] + x[i])
        if trivial: continue
        
        factors = []
        
        for factor, _ in factor_list(g)[1]:
            p = Poly(factor, x, domain=GF(2))
            if p.is_linear or depthLeft <= 0:
                if negate:
                    factors.append(Not(alg_decode_term(factor)))
                else:
                    factors.append(alg_decode_term(factor))
            else:
                dec = alg_decode_term(factor+1)
                mini = minimize(dec, x, depthLeft-1, not negate)
                output.append(mini)
        if negate:
            output.append(Or(*factors))
        else:
            output.append(And(*factors))
    if negate:
        return And(*output)
    else:
        return Or(*output)
    
    
from .expressionast import *
from .equalityprovider import *

def _sympy_to_ast(expr):
    if isinstance(expr, Or):
        args = expr.args
        if len(args) == 0: return I64Node(0)
        r = _sympy_to_ast(args[0])
        for i in range(1, len(args)):
            r = r | _sympy_to_ast(args[i])
        return r
    elif isinstance(expr, And):
        args = expr.args
        if len(args) == 0: return I64Node(-1)
        r = _sympy_to_ast(args[0])
        for i in range(1, len(args)):
            r = r & _sympy_to_ast(args[i])
        return r
    elif isinstance(expr, Xor):
        args = expr.args
        if len(args) == 0: return I64Node(0)
        r = _sympy_to_ast(args[0])
        for i in range(1, len(args)):
            r = r ^ _sympy_to_ast(args[i])
        return r
    elif isinstance(expr, Not):
        return ~_sympy_to_ast(expr.args[0])
    elif isinstance(expr, Symbol):
        return VarNode(expr.name)
    elif isinstance(expr, BooleanTrue):
        return I64Node(-1)
    elif isinstance(expr, BooleanFalse):
        return I64Node(0)
    else:
        print("_sympy_to_ast", type(expr))


class BooleanMinifierProvider(EqualityProvider):

    def __init__(self):
        pass

    def simplify(self, ast):

        is_boolean = map_ast(ast, lambda x: True, lambda y: y == 0 or y == -1, {
        CallType.ADD: lambda a, b: False,
        CallType.SUB: lambda a, b: False,
        CallType.MUL: lambda a, b: False,
        CallType.AND: lambda a, b: a and b,
        CallType.OR: lambda a, b: a and b,
        CallType.XOR: lambda a, b: a and b,
        CallType.SHL: lambda a, b: False,
        CallType.SHR: lambda a, b: False,
        CallType.NOT: lambda a: a,
        CallType.NEG: lambda a: False,
        })

        if not is_boolean: return (False, [])

        sympyVars = {varname: symbols(varname) for varname in get_vars_from_ast(ast)}

        if len(sympyVars) < 2: return (False, [])
        
        sympyTerm = map_ast(ast, lambda x: sympyVars[x], lambda y: True if y == -1 else False, {
        CallType.AND: lambda a, b: a&b,
        CallType.OR: lambda a, b: a|b,
        CallType.XOR: lambda a, b: a^b,
        CallType.NOT: lambda a: ~a,
        })

        sympyMin = simplify_logic(minimize(sympyTerm, [sympyVars[v] for v in sympyVars]))

        return (True, [_sympy_to_ast(sympyMin)])

    def failed(self, ast):
        pass

    def name(self):
        return "BooleanMinifierProvider"
