from egglog import Expr
from .expressionast import *

class EqualityProvider():
    def simplify(self, ast):
        raise NotImplementedError("Not implemented")
    
    def failed(self, ast):
        raise NotImplementedError("Failed to apply to "+str(ast))
    
    def name(self):
        raise NotImplementedError("Not implemented")