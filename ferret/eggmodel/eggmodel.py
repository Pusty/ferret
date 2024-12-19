from ..expressionast import *
from collections.abc import Iterator
from typing import Tuple, List

class EggModel():

    def extract(self, ast:Node, include_cost:bool=False) -> Tuple[Node,bool] | Node:
        raise NotImplementedError("Not implemented")
    
    def run(self, rounds: int):
        raise NotImplementedError("Not implemented")
    
    def register(self, ast: Node):
        raise NotImplementedError("Not implemented")
    
    def simplify(self, ast: Node) -> Tuple[Node, int]:
        self.register(ast)
        self.run(1)
        return self.extract(ast, include_cost=True)
    
    def union(self, astA: Node, astB: Node):
        raise NotImplementedError("Not implemented")
    
    def cost(self, ast: Node) -> int:
        term, cost = self.extract(ast, include_cost=True)
        return cost
    
    def nodecount(self) -> int:
        raise NotImplementedError("Not implemented")
    
    def extract_all_subexprs(self, root: Node, maxim: int) -> Iterator[Tuple[str, List]]:
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
