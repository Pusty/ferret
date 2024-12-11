from .equalityprovider import EqualityProvider
from .bitvec import *
from .expressionast import *


import plyvel
import json
import os
import array
import hashlib
import z3

META_KEY = b"metadatas"
VARS_KEY = b"variables"
INPUTS_KEY = b"inputs"
SIZE_KEY = b"size"


PROJECT_PATH = os.getcwd()
TABLE_PATH = os.path.join(PROJECT_PATH,"qsynth_table", "test_table")


# TODO: Replace z3 with a faster solver for this specific problem

class QSynthEqualityProvider(EqualityProvider):

    # https://github.com/quarkslab/qsynthesis/tree/master
    # https://quarkslab.github.io/qsynthesis/dev_doc/table.html
    # qsynthesis-table-manager generate -bs 64 --var-num 3 --ops SUB,NEG,ADD,XOR,OR --watchdog 85 --input-num 15 --random-level 7 test-table
    def __init__(self):

        # TODO: Make this database server / client infrastructure so that it can run multiprocess / parallel
        self.table = plyvel.DB(TABLE_PATH)
        self.metas = json.loads(self.table.get(META_KEY))
        self.vrs = list(json.loads(self.table.get(VARS_KEY)).items())
        self.inps = json.loads(self.table.get(INPUTS_KEY))

        #print(self.metas)
        #print(self.vrs)
        #print(self.inps)

        self.verify = True
        self.verifyTimeout = 500
        self.verifyEnd = False

        assert self.metas["hash_mode"] == "MD5"
        for var, bits in self.vrs:
            assert bits == 64


    def _hash(self, outs):
        # hash the values to make table keys
        return hashlib.md5(array.array('Q', outs).tobytes()).digest()
    

    def _lookup(self, ast, var_remapping):

        # evaluate the expressions with the test values
        outs = []
        for inp in self.inps:
            mapping = {}
            for var in inp:
                if var in var_remapping: mapping[var_remapping[var]] = inp[var]
            outs.append(eval_ast(ast, mapping)&0xffffffffffffffff)

        outsSet = set(outs)
        if len(outsSet) == 1: # constant output
            return str(outsSet.pop()).encode("ascii")
        else:
            return self.table.get(self._hash(outs))

    def failed(self, expr: Expr):
        print("Failed to apply QSynth to "+expr_to_str(expr))
        pass

    def name(self) -> str:
        return "QSynthEqualityProvider"
    
    def _lookup_ast(self, ast, var_remapping, placeholders):
        #print("Lookup", ast)
        r = self._lookup(ast, var_remapping)
        makePlaceholder = False

        if r == None:
            exprAst = ast
        else: # found lookup in database
            exprLine = r.decode("ascii")

            # make eval variables (and apply remapping)
            varMap = {}
            for v, bits in self.vrs:
                if v in var_remapping:
                    varMap[v] = BitVec.var(var_remapping[v])
                else:
                    varMap[v] = BitVec.var("?")

            replaceRes = expr_to_ast(eval(exprLine, varMap))


            rejectReplace = False

            # introducing new variable bad
            if not rejectReplace and not (set(get_vars_from_ast(replaceRes)) <= set(get_vars_from_ast(ast))):
                rejectReplace = True

            # increase cost bad
            if not rejectReplace and ast_cost(replaceRes) >= ast_cost(ast):
                rejectReplace = True

            # failing verification (if enabled) bad
            if not rejectReplace and self.verify:
                if not self._verify_ast(ast, replaceRes, timeout=self.verifyTimeout, unsafe=False):
                    rejectReplace = True

            if rejectReplace:
                exprAst = ast # no change
            else:
                exprAst = replaceRes
                makePlaceholder = True
                #print("FOUND!!", ast, "=>", exprAst)
    

        # These are commented out because with quick tests these decreased performance
        # ...needs reevaluation

        # check if constant in ast
        #if isinstance(exprAst, I64Node):
        #    makePlaceholder = True
        
        # check if call with constant
        #if isinstance(exprAst, CallNode) and any([isinstance(child, I64Node) for child in exprAst.children]):
        #     makePlaceholder = True

        if makePlaceholder:
            # substitue either original or lookup result 
            tmpVarName = "placeholder_"+hex(hash(ast_to_str(exprAst))&0xffffffff)
            placeholders[tmpVarName] = exprAst
            #print("Replace",ast_to_str(exprAst),"with", tmpVarName)

            return VarNode(tmpVarName)
        else:
            return exprAst

    def _remap_vars(self, ast):

        # sorted
        vs = get_vars_from_ast(ast)

        # check that the table supports expressions with this many variables
        if len(vs) > len(self.vrs):
            #raise Exception("Too many variables, not supported by the table")
            return None
        
        # map {qsynth var} -> {actual var}
        var_remapping = {}
        for i in range(min(len(vs), len(self.vrs))):
            varName, bits = self.vrs[i]
            var_remapping[varName] = vs[i]

        return var_remapping

    def _synthetize(self, ast):
        #print("Synth", ast)
        var_remapping = self._remap_vars(ast)
        # Too many variables, can't simplify
        if var_remapping == None: return ast
        #print("Remap", var_remapping)
        placeholders = {}
        r = map_ast_bfs(ast, lambda type, values: self._lookup_ast(CallNode(type, values), var_remapping, placeholders))
        #print(r)
        if r != ast:
            r = self._synthetize(r)

        return map_ast(r, lambda x: placeholders[x] if x in placeholders else VarNode(x), lambda y: I64Node(y), lambda type, args: CallNode(type, args))


    def _verify_ast(self, astA, astB, timeout=500, unsafe=True):
        var_names = get_vars_from_ast(astA) + get_vars_from_ast(astB)
        z3Vars = {}
        # Note: This being 8 bit is experimental, should be 64 for full equivalence prove
        for vN in var_names:
            z3Vars[vN] = z3.BitVec(vN, 8) # especially in safe mode, can we maybe just check if this "also" works for 8 bit so speed it up? (instead of 64 bit)
        exprA = eval(ast_to_str(astA), z3Vars)
        exprB = eval(ast_to_str(astB), z3Vars)
        solver = z3.Solver()
        solver.set('timeout', timeout)
        solver.add(exprA != exprB)
        #print(exprA, "!=", exprB)
        if unsafe:
            return solver.check() in [z3.unsat, z3.unknown]
        else:
            return solver.check() in [z3.unsat]

    def simplify(self, expr: Expr) -> tuple[bool, list[Expr]]:
        ast = expr_to_ast(expr)

        # remap table vars to expression vars
        simplified = self._synthetize(ast)
        #print("=>", simplified)

        var_names = get_vars_from_ast(simplified)
        bvVars = {}
        for bvName in var_names:
            bvVars[bvName] = BitVec.var(bvName)
        
        oexpr = eval(ast_to_str(simplified), {}, bvVars)
        if isinstance(oexpr, int):
            if oexpr > 0x7fffffffffffffff:
                oexpr = oexpr-0x10000000000000000
            if oexpr < -0x7fffffffffffffff:
                oexpr = oexpr+0x10000000000000000
            oexpr = BitVec(oexpr)


        # Z3 verify overall simplification is correct
        if self.verifyEnd:
            # unsafe quick check is ok here if we only do safe replacements
            if self._verify_ast(ast, simplified, timeout=500, unsafe=True):
                return (True, [oexpr])
            else:
                return (False, [])

        #print(expr_to_str(expr) ,"=>", expr_to_str(oexpr))

        return (True, [oexpr])