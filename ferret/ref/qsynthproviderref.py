from ..equalityprovider import EqualityProvider
from ..expressionast import *


import os
PROJECT_PATH = os.getcwd()
TABLE_PATH = os.path.join(PROJECT_PATH,"qsynth_table", "test_table")



class QSynthEqualityProviderReference(EqualityProvider):

    # https://github.com/quarkslab/qsynthesis/tree/master
    # https://quarkslab.github.io/qsynthesis/dev_doc/table.html
    def __init__(self):
        from triton import TritonContext, ARCH, SOLVER, MODE, AST_REPRESENTATION
        self.ctx = TritonContext(ARCH.X86_64)
        self.ctx.setSolver(SOLVER.Z3)
        self.ctx.setMode(MODE.ALIGNED_MEMORY, True)
        self.ctx.setMode(MODE.AST_OPTIMIZATIONS, True)
        self.ctx.setMode(MODE.CONSTANT_FOLDING, True)
        self.ctx.setMode(MODE.ONLY_ON_SYMBOLIZED, True)
        self.ctx.setAstRepresentationMode(AST_REPRESENTATION.PYTHON)

        from qsynthesis import TopDownSynthesizer, InputOutputOracleLevelDB
        self.table = InputOutputOracleLevelDB.load(TABLE_PATH)
        self.synthesizer = TopDownSynthesizer(self.table) 


    def failed(self, expr):
        print("Failed to apply QSynth Reference to "+expr)
        pass

    def name(self) -> str:
        return "QSynthEqualityProviderReference"
    
    def simplify(self, oast: Node) -> tuple[bool, list[Node]]:
        var_names = get_vars_from_ast(oast)

        ast = self.ctx.getAstContext()

        var_dict = {}
        for var_name in var_names:
            var_dict[var_name] = ast.variable(self.ctx.newSymbolicVariable(64, var_name))

        tritonExpr = eval(ast_to_str(oast), {}, var_dict) + ast.bv(0, 64)
        from qsynthesis import TritonAst
        tritonAst = TritonAst.make_ast(self.ctx, tritonExpr)

        synt_rax, simp_bool = self.synthesizer.synthesize(tritonAst)

        #print(f"simplified: {simp_bool}")
        #print(f"synthesized expression: {synt_rax.pp_str}")
        #print(f"size: {synt_rax.node_count} -> {synt_rax.node_count}")

        oexpr = str_to_ast(synt_rax.pp_str, var_names)
        #print(expr_to_str(expr) ,"=>", expr_to_str(oexpr))

        return (True, [oexpr])