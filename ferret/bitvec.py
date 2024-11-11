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
    
    
import ast as ast_module
def expr_to_str(expr, opt=True):
    ast = expr_to_ast(expr)
    ast_str = ast_to_str(ast)
    if opt:
        ast_str = ast_module.unparse(ast_module.parse(ast_str))
    return ast_str

def get_vars_from_expr(expr):
    ast = expr_to_ast(expr)
    return get_vars_from_ast(ast)
    # sorted(set(re.findall(r'BitVec\.var\("([^"]+)"\)', str(expr))))

def eval_expr(expr, varMap):
    ast = expr_to_ast(expr)
    v = eval_ast(ast, varMap)
    if v > 0x7fffffffffffffff:
        v = v-0x10000000000000000
    if v < -0x7fffffffffffffff:
        v = v+0x10000000000000000
    return v


    
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