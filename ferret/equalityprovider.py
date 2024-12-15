from egglog import Expr
from .expressionast import *

class EqualityProvider():
    def simplify(self, ast: Node) -> tuple[bool, list[Node]]:
        raise NotImplementedError("Not implemented")
    
    def failed(self, ast: Node):
        raise NotImplementedError("Failed to apply to "+str(ast))
    
    def name(self) -> str:
        raise NotImplementedError("Not implemented")