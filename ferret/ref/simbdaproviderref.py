from ..equalityprovider import EqualityProvider
from ..expressionast import *


import os
import sys

PROJECT_PATH = os.getcwd()
TABLE_PATH = os.path.join(PROJECT_PATH,"qsynth_table", "test_table")



PROJECT_PATH = os.getcwd()

SiMBA_PATH = os.path.join(PROJECT_PATH,"thirdparty", "SiMBA")

sys.path.append(os.path.join(
    SiMBA_PATH, "src"
))



class SiMBAEqualityProviderReference(EqualityProvider):

    # https://github.com/DenuvoSoftwareSolutions/SiMBA/tree/main
    def __init__(self, useZ3=False, checkLinear=False):
        self.useZ3 = useZ3
        self.checkLinear = checkLinear

    def failed(self, expr):
        print("Failed to apply SiMBA Reference to "+expr)
        pass

    def name(self) -> str:
        return "SiMBAEqualityProviderReference"
    
    def simplify(self, oast: Node) -> tuple[bool, list[Node]]:
        from simplify import simplify_linear_mba

        var_names = get_vars_from_ast(oast)
        simplifiedStr = simplify_linear_mba(ast_to_str(oast), 64, self.useZ3, self.checkLinear)
        simplified = str_to_ast(simplifiedStr, var_names)

        return (True, [simplified])
