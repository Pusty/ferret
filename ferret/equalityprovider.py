from egglog import Expr
from .expressionast import *
from .bitvec import ast_to_expr

class EqualityProvider():
    def simplify(self, expr: Node) -> tuple[bool, list[Node]]:
        raise NotImplementedError("Not implemented")
    
    def failed(self, expr: Node):
        raise NotImplementedError("Failed to apply to "+str(expr))
    
    def name(self) -> str:
        raise NotImplementedError("Not implemented")
    
    def simplifyExpr(self, expr: Expr) -> tuple[bool, list[Node]]:
        ast = expr_to_ast(expr)
        worked, tup = self.simplify(ast)
        otup = [ast_to_expr(t) for t in tup]
        return (worked, otup)