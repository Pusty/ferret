from .equalityprovider import EqualityProvider
from .expressionast import *

from .solvers import verify_ast

import plyvel
import json
import os
import array
import hashlib

META_KEY = b"metadatas"
VARS_KEY = b"variables"
INPUTS_KEY = b"inputs"
SIZE_KEY = b"size"


PROJECT_PATH = os.getcwd()
TABLE_PATH = os.path.join(PROJECT_PATH,"qsynth_table", "msynth_oracle")


class QSynthEqualityProvider(EqualityProvider):

    # https://github.com/quarkslab/qsynthesis/tree/master
    # https://quarkslab.github.io/qsynthesis/dev_doc/table.html
    # qsynthesis-table-manager generate -bs 64 --var-num 3 --ops SUB,NEG,ADD,XOR,OR --watchdog 85 --input-num 15 --random-level 7 test-table
    def __init__(self, dbserver=False, verify=True, verifyReducedPrecision=True, verifyTimeout=500,verifyEnd=False):

        # if using dbserver, connect to Manager when actually trying to simplify
        self.dbserver = dbserver
        if dbserver == False:
            self.table = plyvel.DB(TABLE_PATH)
            self.metas = json.loads(self.table.get(META_KEY))
            self.vrs = list(json.loads(self.table.get(VARS_KEY)).items())
            self.inps = json.loads(self.table.get(INPUTS_KEY))

            assert self.metas["hash_mode"] == "MD5"
            for var, bits in self.vrs:
                assert bits == 64
        else:
            self.table = None
            self.metas = None
            self.vrs = None
            self.inps = None

        self.verify = verify
        self.verifyReducedPrecision = verifyReducedPrecision
        self.verifyTimeout = verifyTimeout
        self.verifyEnd = verifyEnd

    def _verify_connected(self):
        if self.dbserver and self.table == None:
            from .qsynthdbserver import connectQSynthProvider
            connectQSynthProvider(self)
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

    def failed(self, ast: Node):
        print("Failed to apply QSynth to", ast)
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
                    varMap[v] = VarNode(var_remapping[v])
                else:
                    varMap[v] = VarNode("?")

            replaceRes = str_to_ast(exprLine, varMap)

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
        return verify_ast(astA, astB, {"timeout": timeout, "unsafe": unsafe, "precision": 8 if self.verifyReducedPrecision else 64})

    def simplify(self, ast: Node) -> tuple[bool, list[Node]]:

        self._verify_connected() # check if connected to db if needed

        # remap table vars to expression vars
        simplified = self._synthetize(ast)
        #print("=>", simplified)

        # SMT verify overall simplification is correct
        if self.verifyEnd:
            # unsafe quick check is ok here if we only do safe replacements
            if self._verify_ast(ast, simplified, timeout=500, unsafe=True):
                return (True, [simplified])
            else:
                return (False, [])

        #print(expr_to_str(expr) ,"=>", expr_to_str(oexpr))

        return (True, [simplified])