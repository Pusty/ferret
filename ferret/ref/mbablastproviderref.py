import os
import sys

PROJECT_PATH = os.getcwd()

MBA_BLAST_PATH = os.path.join(PROJECT_PATH,"thirdparty", "MBA-Blast")

sys.path.append(os.path.join(
    MBA_BLAST_PATH, "mba-simplifier"
))
sys.path.append(os.path.join(
    MBA_BLAST_PATH, "tools"
))

import truthtable_simplify as mba_blast


import re
import traceback

# modify for correct path
def get_entire_bitwise(vnumber):
    if not vnumber in [1, 2,3,4]:
        print("vnumber must be 1, 2,3 or 4.")
        traceback.print_stack()
        sys.exit(0)
    truthfile = os.path.join(MBA_BLAST_PATH, "dataset", "{vnumber}variable_truthtable.txt".format(vnumber=vnumber))
    bitList = []
    with open(truthfile, "r") as fr:
        for line in fr:
            if "#" not in line:
                line = line.strip()
                itemList = re.split(",", line)
                bit = itemList[1]
                bitList.append(bit)

    return bitList

mba_blast.get_entire_bitwise = get_entire_bitwise
# depreciated
mba_blast.np.int = int


from ..equalityprovider import EqualityProvider
from ..bitvec import *



class MBABlastEqualityProviderReference(EqualityProvider):

    def __init__(self):
        pass

    def simplify(self, expr: Expr) -> tuple[bool, list[Expr]]:
        str_expr = expr_to_str(expr, opt=True) 
        #.. mba-blasts parser is too fragile to parse redudant brackets..
        str_expr = str_expr.replace(" ", "")
        

        (simExpre, vnumber, replaceStr) = mba_blast.simplify_MBA(str_expr)
        simExpre = mba_blast.refine_mba(simExpre, vnumber)

        #print(simExpre)

        if len(replaceStr) == 2:
            simExpre = simExpre.replace("x", replaceStr[0]).replace("y", replaceStr[1])
        elif len(replaceStr) == 3:
            simExpre = simExpre.replace("x", replaceStr[0]).replace("y", replaceStr[1]).replace("z", replaceStr[2])
        else:
            print("bug in simplify_dataset")
            return (False, [])

        #print("complex MBA expression: ", str_expr)
        #print("after simplification:   ", simExpre)

        # hardcode this for now because this probably won't be used in the final thing anyways
        a = BitVec.var("a")
        b = BitVec.var("b")
        c = BitVec.var("c")
        d = BitVec.var("d")
        e = BitVec.var("e")
        f = BitVec.var("f")
        x = BitVec.var("x")
        y = BitVec.var("y")
        z = BitVec.var("z")
        t = BitVec.var("t")

        res = eval(simExpre)
        # if optimized is just a number
        if isinstance(res, int):
            res = BitVec(res)


        return (True, [res])


    def name(self) -> str:
        return "MBABlastEqualityProviderReference"