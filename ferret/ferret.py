from .bitvec import *
from .equalityprovider import *
from egglog import *
import json
import random

# Project Root

def create_graph() -> EGraph:
    egg = EGraph()
    egg.register(*BitVec_rules())
    return egg

def cost(egg: EGraph, expr: Expr) -> int:
    egg.register(expr)
    out_expr, cost = egg.extract(expr, include_cost=True)
    return cost

def simplify(egg: EGraph, expr: Expr) -> tuple[Expr, int]:
    egg.register(expr)
    egg.run(1)
    simp = egg.extract(expr, include_cost=True)
    return simp

def apply_eqprov(egg: EGraph, eqprov: EqualityProvider, expr: Expr):
    bef_expr, bef_cost = egg.extract(expr, include_cost=True)
    success, sexprs = eqprov.simplifyExpr(expr)
    if success:
        for sexpr in sexprs: 
            egg.register(union(expr).with_(sexpr))
            assert_oracle_equality(expr, sexpr)
    else:
        eqprov.failed(expr_to_ast(expr))
        return None
    aft_expr, aft_cost = egg.extract(expr, include_cost=True)
    return (aft_expr, bef_cost, aft_cost)
    
def iter_simplify(egg: EGraph, expr: Expr, eqprovs: list[EqualityProvider]=[], inner_max: int=20, max_nodes: int=25000):
    init_cost = cost(egg, expr)

    for eqprov in eqprovs:
        v = apply_eqprov(egg, eqprov, expr)

    last_amount_nodes = 0
    last_cost = cost(egg, expr)

    for i in range(inner_max):
        
        expr, last_cost = simplify(egg, expr)

        for eqprov in eqprovs:
            v = apply_eqprov(egg, eqprov, expr)
 
        last_cost = cost(egg, expr)

        p = json.loads(egg._egraph.serialize([],
            max_functions=None,
            max_calls_per_function=None,
            include_temporary_functions=False).to_json())
        amount_nodes = len(p["nodes"])
        # probably explodes
        if amount_nodes > max_nodes: break
        # saturated
        if last_amount_nodes == amount_nodes: break
        last_amount_nodes = amount_nodes

    return init_cost, last_cost

def test_oracle_equality(exprA: Expr, exprB: Expr, N=10, doAssert=False):
    astA = expr_to_ast(exprA)
    astB = expr_to_ast(exprB)
    varsA = get_vars_from_ast(astA)
    varsB = get_vars_from_ast(astB)
    varsAB = set(varsA) | set(varsB)
    varMap = {}
    for i in range(N):
        for v in varsAB:
            varMap[v] = random.randint(0, 0xffffffffffffffff)
        evalA = eval_expr(exprA, varMap)
        evalB = eval_expr(exprB, varMap)
        if doAssert:
            assert evalA  == evalB , expr_to_str(exprA) + " != " + expr_to_str(exprB)+" for "+str(varMap)+" resulting in "+str((evalA, evalB))
        else:
            if evalA != evalB: return False
    return True
    

def assert_oracle_equality(exprA: Expr, exprB: Expr, N=10):
    return test_oracle_equality(exprA, exprB, N=N, doAssert=True)

def test_stuff():
    g = create_graph()
    simp, cost = simplify(g, BitVec(5))
    print(simp, cost)