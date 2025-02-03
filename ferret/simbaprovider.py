from .equalityprovider import EqualityProvider
from .expressionast import *

import itertools
import numpy as np

from pyeda.inter import exprvar, espresso_tts
from pyeda.boolalg.table import truthtable
import pyeda

import sympy
from .solvers import verify_ast

class SiMBAEqualityProvider(EqualityProvider):

    # https://github.com/DenuvoSoftwareSolutions/SiMBA/blob/main/paper/paper.pdf
    def __init__(self, allowNonLinear=True, decomposeQuick=True):
        self.allowNonLinear = allowNonLinear
        self.decomposeQuick = decomposeQuick

    def failed(self, expr):
        pass

    def name(self):
        return "SiMBAEqualityProvider"
    
    def _ast_to_signature(self, ast, varnames):
        truthtable = []
        varnames = varnames
        for i in range(1<<len(varnames)):
            varMap = {}
            for j, n in enumerate(varnames):
                varMap[n] = ((i >> j) & 1)
            truthtable.append(sign_i64(eval_ast(ast, varMap)))
        return truthtable
    
    def _and_all(self, var_indxs, expr_vars):
        if len(var_indxs) == 0: return I64Node(-1)
        v = VarNode(expr_vars[var_indxs[0]])
        for i in range(1, len(var_indxs)):
            v = CallNode(CallType.AND, [v, VarNode(expr_vars[var_indxs[i]])])
        return v
    
    def _add_all(self, terms):
        if len(terms) == 0: return I64Node(0)
        v = terms[0]
        for i in range(1, len(terms)):
            v = CallNode(CallType.ADD, [v, terms[i]])
        return v
    
    def _signature_to_coefficients(self, signatureVector, var_amount):
        basis = []
        line = [0]*len(signatureVector)
        line[0] = 1
        basis.append(line)

        for i in range(1, 1 << var_amount):
            entry = [j for j in range(var_amount) if (i & (1 << j))]
            line = [0]*len(signatureVector)
            line[0] = 1
            for j in range(1, 1 << len(entry)):
                indx = sum([1<<entry[l] for l in range(len(entry)) if (j & (1 << l))])
                line[indx] = 1
            basis.append(line)

        A = sympy.Matrix(basis)
        b = sympy.Matrix(signatureVector)
        r = A.solve(b).T
        l = [round(i) for i in r.tolist()[0]]
        return l
    
    def inner_simplify(self, signatureVector, expr_vars):
        if len(expr_vars) == 0: return I64Node(signatureVector[0])
        terms = []
        coeffs = self._signature_to_coefficients(signatureVector, len(expr_vars))
        if(coeffs[0] != 0):
            terms.append(I64Node(coeffs[0]))

        for i in range(1, 1 << len(expr_vars)):
            var_indxs = [j for j in range(len(expr_vars)) if (i & (1 << j))]
            index = sum(1<<i for i in var_indxs)
            coeff = coeffs[index]
            if coeff == 0: continue

            term = self._and_all(var_indxs, expr_vars)
            if coeff != 1:
                if coeff == -1:
                    term = CallNode(CallType.NEG, [term])
                else:
                    term = CallNode(CallType.MUL, [I64Node(coeff), term])
            terms.append(term)
        simplify_result = self._add_all(terms)
        return simplify_result

    def pyeda_to_ast(self, expr):
        if isinstance(expr, pyeda.boolalg.expr.OrOp):
            args = expr.xs
            if len(args) == 0: return I64Node(0)
            r = self.pyeda_to_ast(args[0])
            for i in range(1, len(args)):
                r = r | self.pyeda_to_ast(args[i])
            return r
        elif isinstance(expr, pyeda.boolalg.expr.AndOp):
            args = expr.xs
            if len(args) == 0: return I64Node(-1)
            r = self.pyeda_to_ast(args[0])
            for i in range(1, len(args)):
                r = r & self.pyeda_to_ast(args[i])
            return r
        elif isinstance(expr, pyeda.boolalg.expr.XorOp):
            args = expr.xs
            if len(args) == 0: return I64Node(0)
            r = self.pyeda_to_ast(args[0])
            for i in range(1, len(args)):
                r = r ^ self.pyeda_to_ast(args[i])
            return r
        elif isinstance(expr, pyeda.boolalg.expr.Complement):
            return ~self.pyeda_to_ast(expr.__invert__())
        elif isinstance(expr, pyeda.boolalg.expr.Variable):
            return VarNode(expr.name)
        elif isinstance(expr, pyeda.boolalg.expr._One):
            return I64Node(-1)
        elif isinstance(expr, pyeda.boolalg.expr._Zero):
            return I64Node(0)
        else:
            raise Exception("pyeda_to_ast"+str(type(expr)))

    def lookup_signature(self, signature, expr_vars):
        vars = [exprvar(v) for v in expr_vars]
        tt = truthtable(vars, signature)
        simplified = espresso_tts(tt)[0]
        return self.pyeda_to_ast(simplified)

    def decompose(self, signature, expr_vars):
        basisVectors = []

        xs = range(len(signature)-1)
        count = 2 if self.decomposeQuick else 3
        for entry in itertools.chain.from_iterable(itertools.combinations(xs,n) for n in range(1, count)):
            basis = [1 if i in entry else 0 for i in range(len(signature)-1)]
            basisVectors.append(basis)

        basis = np.array(basisVectors).T
        signature = np.array(signature)
        amount_basis = basis.shape[1]
        basisVars = sympy.symbols(f'c0:{amount_basis}')
        equations = [sum(basis[i-1, j] * basisVars[j] for j in range(amount_basis)) - signature[i] for i in range(1, len(signature))]
        result = sympy.solve(equations, set=True, minimal=True, numerical=True, particular=True, quick=self.decomposeQuick)
        if result == []: return None
        mapping, solutions = result
        solutions = list(solutions)
        if len(solutions) == 0: return None
        solution = solutions[0]
        terms = []
        for basisIndex in range(len(basisVars)):
            mappingIndex = mapping.index(basisVars[basisIndex])
            coeff = solution[mappingIndex]
            if coeff == 0: continue
            term = self.lookup_signature([0]+basisVectors[basisIndex], expr_vars)
            if coeff != 1:
                if coeff == -1:
                    term = CallNode(CallType.NEG, [term])
                else:
                    term = CallNode(CallType.MUL, [I64Node(coeff), term])
            terms.append(term)
        return self._add_all(terms)

    def inner_refine(self, oast):
        expr_vars = get_vars_from_ast(oast)
        signatureVector = self._ast_to_signature(oast, expr_vars)
        uniqueSignature = list(set(signatureVector))

        multiplyFactor = 1
        additionOffset = 0
        negate = False

        # constant expression (refine case 1)
        if len(uniqueSignature) == 1: return I64Node(signatureVector[0])

        # multiply factor (refine case 2)
        if len(uniqueSignature) == 2:
            if signatureVector[0] == 0:
                for i in range(len(signatureVector)):
                    if signatureVector[i] != 0:
                        multiplyFactor = signatureVector[i]
                        signatureVector[i] = 1
            else:
                a = signatureVector[0]
                b = [x for x in signatureVector if x != a][0] 
                if b == sign_i64(a * 2): # case 3
                    multiplyFactor = -a
                    negate=True
                    for i in range(len(signatureVector)):
                        if signatureVector[i] == a:
                            signatureVector[i] = 0
                        elif signatureVector[i] == b:
                            signatureVector[i] = 1

        if signatureVector[0] != 0:
            additionOffset = signatureVector[0]
            for i in range(len(signatureVector)):
                signatureVector[i] = sign_i64(signatureVector[i] - additionOffset)

        uniqueSignatureAfter = list(set(signatureVector))
        uniqueSignatureAfter.remove(0)

        simplify_result = None
        if len(uniqueSignatureAfter) == 1:
            for i in range(len(signatureVector)):
                if signatureVector[i] != 0 and signatureVector[i] != 1:
                    multiplyFactor = signatureVector[i]
                    signatureVector[i] = 1
            simplify_result = self.lookup_signature(signatureVector, expr_vars)
        else:
            # decompose into (somewhat) minimal list of binary basis vectors and look them up by signature
            # case 5: (0, 3735936685, 3735936685, 49374) -> (0, 0, 0, a) (0, b, b, 0) -> 49374 (x&y) + 3735936685 (x^y).
            # case 6:  (0, 3735936685, 3735887311, 49374) ->  (0, a, a, 0) (0, b, 0, b) -> 3735887311 (x^y) + 49374 x
            # case 7:  (0, 49374, 3735936685, 201) ->  (0, a, 0, 0)  (0, 0, b, 0)  (0, 0, 0, c) -> 49374 (x & ∼y) + 3735936685 · ∼(x | ∼y) + 201 (x & y)
            simplify_result = self.decompose(signatureVector, expr_vars)
            if simplify_result == None: return None


        if simplify_result == None:
            # fallback to just inner simplify
            simplify_result = self.inner_simplify(signatureVector, expr_vars)
            if simplify_result == None: return None

        if negate:
            simplify_result = CallNode(CallType.NOT, [simplify_result])

        if multiplyFactor != 1:
            if multiplyFactor == -1:
                simplify_result = CallNode(CallType.NEG, [simplify_result])
            else:
                simplify_result = CallNode(CallType.MUL, [I64Node(multiplyFactor), simplify_result])

        if additionOffset != 0:
            simplify_result = CallNode(CallType.ADD, [I64Node(additionOffset), simplify_result])

        return simplify_result
    
    def apply_simplify(self, oast):
        expr_vars = get_vars_from_ast(oast)
        signatureVector = self._ast_to_signature(oast, expr_vars)
        return self.inner_simplify(signatureVector, expr_vars)
    
    def apply_func(self, options, func, original, non_linear):
        options.sort(key=lambda x: x[0])
        r = func(options[0][1])
        if r == None: 
            if len(options) == 1 or options[0][1] == original: 
                return False
            else: 
                return True
            
        if non_linear and not verify_ast(original, r, {"timeout": 250, "unsafe": True, "precision": 8}): 
            return True
         
        options.append((ast_cost(r), r))
        return True


    def simplify(self, oast):
        non_linear = not is_linear(oast)
        if non_linear and not self.allowNonLinear: return (False, [])

        options = [(ast_cost(oast), oast)]

        if not self.apply_func(options, self.apply_simplify, oast, non_linear):
            return (False, [])
        if len(get_vars_from_ast(options[0][1])) > 2:
            if not self.apply_func(options, self.apply_simplify, oast, non_linear):
                return (False, [])
            
        if not self.apply_func(options, self.inner_refine, oast, non_linear):
            return (False, [])
            
        options.sort(key=lambda x: x[0])
        res = options[0][1]

        if res == oast:
            if len(options) > 1:
                return (True, [options[1][1]])
            return (False, [])

        return (True, [res])