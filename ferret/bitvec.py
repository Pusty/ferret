from __future__ import annotations
from egglog import *
from egglog.declarations import *

from .expressionast import *


class BitVec(Expr):
    def __init__(self, value: i64) -> None: ...

    @classmethod
    def var(cls, name: StringLike) -> BitVec: ...

    def __add__(self, other: BitVec) -> BitVec: ...
    def __sub__(self, other: BitVec) -> BitVec: ...
    def __mul__(self, other: BitVec) -> BitVec: ...
    def __and__(self, other: BitVec) -> BitVec: ...
    def __or__(self, other: BitVec) -> BitVec: ...
    def __xor__(self, other: BitVec) -> BitVec: ...
    def __lshift__(self, other: BitVec) -> BitVec: ...
    def __rshift__(self, other: BitVec) -> BitVec: ...
    def __invert__(self) -> BitVec: ...
    def __neg__(self) -> BitVec: ...
    
    
#import ast as ast_module
def expr_to_str(expr, opt=True):
    ast = expr_to_ast(expr)
    ast_str = ast_to_str(ast)
    if opt:
        ast_str = ast_module.unparse(ast_module.parse(ast_str))
    return ast_str


def eval_expr(expr, varMap):
    ast = expr_to_ast(expr)
    v = eval_ast(ast, varMap)
    if v > 0x7fffffffffffffff:
        v = v-0x10000000000000000
    if v < -0x7fffffffffffffff:
        v = v+0x10000000000000000
    return v

def ast_to_expr(ast):
    def adjust_const(val):
        if val > 0x7fffffffffffffff:
            val = val-0x10000000000000000
        if val < -0x7fffffffffffffff:
            val = val+0x10000000000000000
        return val
    
    return map_ast(ast,
        lambda var: BitVec.var(var), 
        lambda val: BitVec(adjust_const(val)), {
        CallType.ADD: lambda a, b: (a+b),
        CallType.SUB: lambda a, b: (a-b),
        CallType.MUL: lambda a, b: (a*b),
        CallType.AND: lambda a, b: (a&b),
        CallType.OR: lambda a, b: (a|b),
        CallType.XOR: lambda a, b: (a^b),
        CallType.SHL: lambda a, b: (a<<b),
        CallType.SHR: lambda a, b: (a>>b),
        CallType.NOT: lambda a: (~a),
        CallType.NEG: lambda a: (-a)
    })


"""
def ast_to_expr(ast):
    var_names = get_vars_from_ast(ast)
    var_map = {}
    for var_name in var_names:
        var_map[var_name] = BitVec.var(var_name)
    res = eval(ast_to_str(ast), {}, var_map)
    if isinstance(res, int):
        if res > 0x7fffffffffffffff:
            res = res-0x10000000000000000
        if res < -0x7fffffffffffffff:
            res = res+0x10000000000000000
        res = BitVec(res)
    return res
"""

import itertools
import json

def _traverse_egraph_nodes(nodes, cur, eclasses, nodeclass, seen, subexprs, maxim):
    if cur in seen: return
    if maxim != -1 and len(subexprs) >= maxim: return
    # don't travel the same path twice
    seen = seen | set([cur])
    # for every node in this equivalence class
    for node in eclasses[cur]:
        # all products of child equivalent classes
        for args in itertools.product(*[_traverse_egraph_nodes(nodes, nodeclass[child], eclasses, nodeclass, seen, subexprs, maxim) for child in nodes[node]["children"]]):
            if maxim != -1 and len(subexprs) >= maxim: return
            r = (nodes[node]["op"], args)
            # add subexprs to output set
            subexprs.add(r)
            # yield for one layer up in recursion
            yield r

def _json_to_expr(subexpr):
    f, arg = subexpr
    
    if not f.startswith("BitVec"):
        if f.startswith('"'): # var
            return f[1:-1]
        else: # or num
            return int(f)
    elif f == "BitVec___add__":
        return _json_to_expr(arg[0]) + _json_to_expr(arg[1])
    elif f == "BitVec___sub__":
        return _json_to_expr(arg[0]) - _json_to_expr(arg[1])
    elif f == "BitVec___mul__":
        return _json_to_expr(arg[0]) * _json_to_expr(arg[1])
    elif f == "BitVec___and__":
        return _json_to_expr(arg[0]) & _json_to_expr(arg[1])
    elif f == "BitVec___or__":
        return _json_to_expr(arg[0]) | _json_to_expr(arg[1])
    elif f == "BitVec___xor__":
        return _json_to_expr(arg[0]) ^ _json_to_expr(arg[1])
    elif f == "BitVec___lshift__":
        return _json_to_expr(arg[0]) << _json_to_expr(arg[1])
    elif f == "BitVec___rshift__":
        return _json_to_expr(arg[0]) >> _json_to_expr(arg[1])
    elif f == "BitVec___invert__":
        return ~_json_to_expr(arg[0])
    elif f == "BitVec___neg__":
        return -_json_to_expr(arg[0])
    elif f == "BitVec___init__":
        return BitVec(_json_to_expr(arg[0]))
    elif f == "BitVec_var":
        return BitVec.var(_json_to_expr(arg[0]))
            
    else:
        raise Exception("Invalid function", f)
        

egg_json_to_expr = _json_to_expr

# extremely inefficient as we get the egraph as json
# then need to get the subexpressions
# then need to convert back to python
def egg_extract_all_subexpr(egg, rootExpr, maxim=-1):
    _root = egg._state.typed_expr_to_egg(expr_parts(rootExpr))

    json_egraph = egg._egraph.serialize([_root],
        max_functions=None,
        max_calls_per_function=None,
        include_temporary_functions=False).to_json()
    #print(json_egraph)
    json_egraph = json.loads(json_egraph)

    # start extracting subexpr from here
    root = json_egraph["root_eclasses"][0]
    eclasses = {}
    nodeclass = {}
    for cl in json_egraph["class_data"]:
        eclasses[cl] = set()
        
    for nodeID in json_egraph["nodes"]:
        node = json_egraph["nodes"][nodeID]
        eclasses[node["eclass"]].add(nodeID)
        nodeclass[nodeID]= node["eclass"]
    
    subexprs = set()
    # fill the subexprs set
    for r in _traverse_egraph_nodes(json_egraph["nodes"], root, eclasses,nodeclass, set(), subexprs, maxim):
        pass

    for r in subexprs:
        # skip raw numbers and var names
        if not r[0].startswith("BitVec"): continue
        yield r #_json_to_expr(r)
        
    
def BitVec_rules() -> list[RewriteOrRule]:
    x, y, z = vars_("x y z", BitVec)
    i, j = vars_("i j", i64)
    return [

    # Constant simplification
    rewrite(BitVec(i) + BitVec(j)).to(BitVec(i + j)),
    rewrite(BitVec(i) - BitVec(j)).to(BitVec(i - j)),
    rewrite(BitVec(i) & BitVec(j)).to(BitVec(i & j)),
    rewrite(BitVec(i) | BitVec(j)).to(BitVec(i | j)),
    rewrite(BitVec(i) ^ BitVec(j)).to(BitVec(i ^ j)),
    rewrite(BitVec(i) << BitVec(j)).to(BitVec(i << j)),
    rewrite(BitVec(i) >> BitVec(j)).to(BitVec(i >> j)),
    rewrite(BitVec(i) * BitVec(j)).to(BitVec(i * j)),

    # Commutativity
    rewrite(x*y).to(y*x),
    rewrite(x+y).to(y+x),
    rewrite(x&y).to(y&x),
    rewrite(x^y).to(y^x),
    rewrite(x|y).to(y|x),
    # Associativity
    rewrite(x*(y*z)).to((x*y)*z),
    rewrite((x*y)*z).to(x*(y*z)),
    rewrite(x+(y+z)).to((x+y)+z),
    rewrite((x+y)+z).to(x+(y+z)),
    rewrite(x&(y&z)).to((x&y)&z),
    rewrite((x&y)&z).to(x&(y&z)),
    rewrite(x^(y^z)).to((x^y)^z),
    rewrite((x^y)^z).to(x^(y^z)),
    rewrite(x|(y|z)).to((x|y)|z),
    rewrite((x|y)|z).to(x|(y|z)),
    # Normalisation (pushing NotW to the leaves)
    rewrite(~(x*y)).to(((~x)*y)+(y-BitVec(1))),
    rewrite(~(x+y)).to((~x)+((~y)+BitVec(1))),
    rewrite(~(x-y)).to((~x)-((~y)+BitVec(1))),
    rewrite(~(x&y)).to((~x)|(~y)),
    rewrite(~(x^y)).to((x&y)|(~(x|y))),
    rewrite(~(x|y)).to((~x)&(~y)),
    # Normalisation (pushing NegW to the leaves)
    rewrite(-(x*y)).to((-x)*y),
    rewrite(-(x*y)).to(x*(-y)),
    # Equalities
    rewrite(-x).to((~x)+BitVec(1)),
    rewrite((~x)+BitVec(1)).to(-x),
    rewrite(x-y).to(x+(-y)),
    rewrite(x+(-y)).to(x-y),
    
    # Inverse distributivity
    rewrite((x*y)+(x*z)).to(x*(y+z)),
    rewrite((x*y)-(x*z)).to(x*(y-z)),
    
    # Collapsing
    rewrite((x*y)+y).to((x+BitVec(1))*y),
    rewrite(x+x).to(BitVec(2)*x),
    rewrite((x^y)|y).to(x|y),
    
    # Swapping
    rewrite(x*(-y)).to(-(x*y)),
    
    # Distributivity
    rewrite((x+y)*z).to((x*z)+(y*z)),
    rewrite((x-y)*z).to((x*z)-(y*z)),
    
    # Additional rules
    rewrite(-(x+y)).to((-x)+(-y)),
    rewrite((x&y)<<z).to((x<<z)&(y<<z)),
    rewrite((x>>z)<<z).to(x&(~((BitVec(1)<<z)-BitVec(1)))),
    rewrite(y-((~x)&y)).to(x&y),
    rewrite((x<<z)+(y<<z)).to((x+y)<<z),
    rewrite((x<<y)<<z).to((x<<z)<<y),
    
    rewrite((x | y) - (~x & y)).to(x),
    
    # Trivial identities
    rewrite(BitVec(0) + x).to(x),
    rewrite(x - BitVec(0)).to(x),
    rewrite(x * BitVec(1)).to(x),
    rewrite(x & x).to(x),
    rewrite(x | x).to(x),
    rewrite(~(~x)).to(x),
    rewrite(-(-x)).to(x),
    rewrite(x | BitVec(0)).to(x),
    rewrite(x ^ BitVec(0)).to(x),
    rewrite(x >> BitVec(0)).to(x),
    rewrite(x << BitVec(0)).to(x),
    
    rewrite(~(-x)).to(x - BitVec(1)),
    rewrite(-(~x)).to(x + BitVec(1)),
    
    # Null terms
    rewrite(x & BitVec(0)).to(BitVec(0)),
    rewrite(x ^ x).to(BitVec(0)),
    rewrite(x - x).to(BitVec(0)),
    rewrite(x * BitVec(0)).to(BitVec(0)),
    ]


def convert_i64(x):
    v = int(str(x)[4:-1])
    if v > 0x7fffffffffffffff:
        v = v-0x10000000000000000
    if v < -0x7fffffffffffffff:
        v = v+0x10000000000000000
    return BitVec(v)

converter(i64, BitVec, convert_i64)