from ..expressionast import *

class EggModel():

    def extract(self, ast, include_cost=False):
        raise NotImplementedError("Not implemented")
    
    def run(self, rounds):
        raise NotImplementedError("Not implemented")
    
    def register(self, ast):
        raise NotImplementedError("Not implemented")
    
    def simplify(self, ast):
        self.register(ast)
        self.run(1)
        return self.extract(ast, include_cost=True)
    
    def union(self, astA, astB):
        raise NotImplementedError("Not implemented")
    
    def cost(self, ast):
        term, cost = self.extract(ast, include_cost=True)
        return cost
    
    def nodecount(self):
        raise NotImplementedError("Not implemented")
    
    def extract_all_subexprs(self, root, maxim, best=False):
        raise NotImplementedError("Not implemented")

    # save current graph as a display step
    def save_display_step(self):
        raise NotImplementedError("Not implemented")
    
    # display the entire graph
    def display(self):
        raise NotImplementedError("Not implemented")

from .bitvec_basic import EggBasic
from .bitvec_multiset import EggMultiset

EggImpl = EggBasic

def get_eggmodel_impl(name):
    if name == "basic":
        return EggBasic
    elif name == "multiset":
        return EggMultiset
    else:
        raise Exception("Unknown Egg Model "+name)
