from egglog import Expr

class EqualityProvider():
    def simplify(self, expr: Expr) -> tuple[bool, list[Expr]]:
        raise NotImplementedError("Not implemented")
    
    def failed(self, expr: Expr):
        raise NotImplementedError("Failed to apply to "+str(expr))
    
    def name(self) -> str:
        raise NotImplementedError("Not implemented")