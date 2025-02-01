from .equalityprovider import EqualityProvider
from .expressionast import *

import numpy as np
import sympy
import itertools

class MBABlastDoesNotApplyException(Exception):
    pass


# actual rewrite of MBA-Blast instead of integration of existing project
# works for linear expressions that contain pure bit operations with a coefficient in terms seperated by addition/substraction 
class MBABlastEqualityProvider(EqualityProvider):

    def __init__(self):
        self.basisMap = {}

        self.truthbasisMap = {}
        self.placeholderMapping = {}
        self.placeholdersMap = {}

        # Hardcode for var_amount 1 and 2, generate "on request" otherwise
        #self._add_basis(2, [VarNode("B00"), VarNode("B01"), CallNode(CallType.AND, [VarNode("B00"), VarNode("B01")]), 
        #             CallNode(CallType.NOT, [CallNode(CallType.AND, [VarNode("B00"), CallNode(CallType.NOT, [VarNode("B00")])])])], ["B00", "B01"])

    def _add_basis(self, var_amount, basisVec, basisVars):
        truthbasis = []
        for bit in basisVec:
            truthbasis.append(self._ast_to_truthtable(bit, basisVars))
        placeholderMapping = {}
        placeholders = []
        for i in range(len(basisVec)):
            # I'm lazy and doing replace on placeholder names with basis expressions
            # so it is important that there is no overlap in the prefix
            name = "_X%02X_" % i
            placeholders.append(name)
            placeholderMapping[name] = "("+ast_to_str(basisVec[i])+")"

        self.basisMap[var_amount] = basisVec
        self.truthbasisMap[var_amount] = truthbasis
        self.placeholderMapping[var_amount] = placeholderMapping
        self.placeholdersMap[var_amount] = placeholders

    # generate short "AND" basis vectors
    def _generate_basis(self, var_amount):
        basisVec = []
        vars = ["_B%02X_" % i for i in range(var_amount)]
        for i in range(var_amount):
            for comb in itertools.combinations(vars, i+1):
                n = VarNode(comb[0])
                for j in range(1, len(comb)):
                    n = CallNode(CallType.AND, [n, VarNode(comb[j])])
                basisVec.append(n)

        # always true entry    
        basisVec.append(CallNode(CallType.NOT, [CallNode(CallType.AND, [VarNode("_B00_"), CallNode(CallType.NOT, [VarNode("_B00_")])])]))
        self._add_basis(var_amount, basisVec, vars)

    # returns a list of terms that are added together the input term
    def _split_ast(self, ast, bitwise=False):
        if isinstance(ast, VarNode): return ast
        elif isinstance(ast, I64Node):
            if bitwise: raise MBABlastDoesNotApplyException("Constant in Bitwise Expression")
            else:       return ast
        elif isinstance(ast, CallNode):

            # Logic instructions are always ok, but no arithmetic may follow a logic operation
            if ast.value in [CallType.AND, CallType.OR, CallType.XOR, CallType.NOT]:
                bitwise = True
            # If we encountered a logic instruction before and this isn't a logic instruction we can't process this
            elif bitwise:
                raise MBABlastDoesNotApplyException("Arithmetic in Bitwise Expression")
            
            nodes = []
            for arg in ast.children:
                nodes.append(self._split_ast(arg, bitwise))
            
            if ast.value == CallType.ADD:
                a, b = nodes
                if isinstance(a, list) and isinstance(b, list): return a+b
                elif isinstance(a, list): return a+[b]
                elif isinstance(b, list): return [a]+b
                else: return [a, b]
            elif ast.value == CallType.SUB:
                a, b = nodes
                if isinstance(a, list) and isinstance(b, list): return a+[CallNode(CallType.NEG, [x]) for x in b]
                elif isinstance(a, list): return a+[CallNode(CallType.NEG, [b])]
                elif isinstance(b, list): return [a]+[CallNode(CallType.NEG, [x]) for x in b]
                else: return [a, CallNode(CallType.NEG, [b])]
            elif ast.value == CallType.MUL:
                a, b = nodes
                if ((isinstance(a, list) or not isinstance(a, I64Node))) and (isinstance(b, list) or not isinstance(b, I64Node)):
                    raise MBABlastDoesNotApplyException("Not Linear")
                # (x + y) * constant 
                if isinstance(a, list):
                    return [CallNode(CallType.MUL, [b, node]) for node in a]
                # constant * (x + y)
                elif isinstance(b, list):
                    return [CallNode(CallType.MUL, [a, node]) for node in b]
                else:
                    return CallNode(CallType.MUL, nodes)
            elif ast.value == CallType.SHR:
                raise MBABlastDoesNotApplyException("Shift Right in Expression not implemented")
            elif ast.value == CallType.SHL:
                a, b = nodes
                # treat as multiplication 2**shift
                if (isinstance(b, list) or not isinstance(b, I64Node)):
                    raise MBABlastDoesNotApplyException("Not Linear (__lshift__) or not implemented")
                if (isinstance(b, I64Node) and b.value <= 0):
                    raise MBABlastDoesNotApplyException("Weird __lshift__")
                # (x + y) * (2**constant)
                if isinstance(a, list):
                    return [CallNode(CallType.MUL, [I64Node(2**b.value), node]) for node in a]
                else:
                    return CallNode(CallType.MUL, [I64Node(2**b.value), a])
                
            elif ast.value == CallType.NEG:
                a = nodes[0]
                if isinstance(a, list):
                    return [CallNode(CallType.NEG, [node]) for node in a]
                return CallNode(CallType.NEG, nodes)
            else:
                return CallNode(ast.value, nodes)

        else:
            assert(False)

    def _parse_coefficient(self, ast):
        if isinstance(ast, VarNode):
            return (1, ast)
        elif isinstance(ast, I64Node):
            return (ast.value, I64Node(1))
        elif isinstance(ast, CallNode):
            if ast.value == CallType.MUL:
                cof0, sast0 = self._parse_coefficient(ast.children[0])
                cof1, sast1 = self._parse_coefficient(ast.children[1])
                if isinstance(sast0, I64Node) and isinstance(sast1, I64Node):
                    return (cof0*cof1, I64Node(1))
                elif isinstance(sast0, I64Node):
                    return (cof0*cof1, sast1)
                elif isinstance(sast1, I64Node):
                    return (cof0*cof1, sast0)
                else:
                    raise Exception("_parse_coefficient error for multiplication "+str(ast))
            elif ast.value == CallType.NEG:
                cof, sast = self._parse_coefficient(ast.children[0])
                return (-cof, sast)
            else:
                return (1, ast)
        else:
            assert(False)
            

    def _ast_to_truthtable(self, ast, varnames):
        truthtable = []
        varnames = varnames
        for i in range(2**len(varnames)):
            varMap = {}
            for j, n in enumerate(varnames):
                varMap[n] = ((i >> j) & 1)
            truthtable.append(eval_ast(ast, varMap)&1)
        return truthtable
    

    def _truthtable_to_coefficients(self, truthtable, var_amount):
        A = np.asmatrix(self.truthbasisMap[var_amount], dtype=np.int64).T
        b = np.asmatrix(truthtable, dtype=np.int64).T
        r = np.linalg.solve(A, b)
        l = [round(i) for i in np.array(r).reshape(-1,).tolist()]
        # would be smart to cache l for truthtable key
        return l

    
    def simplify(self, ast):
        var_names = get_vars_from_ast(ast)
        var_amount = len(var_names)

        if var_amount == 0:
            return (False, [])
        
        # If the amount of variables has no registered basis cached generate it
        if not var_amount in self.basisMap:
            self._generate_basis(var_amount)
        
        #print(ast)

        # 1. Split terms, verify only bitwise within subterms (which have a coefficient), make sure it is linear
        # (If not linear or contains arithmetic expressions or constants in logical subexpresisons will throw an exception )
        try:
            split_ast = self._split_ast(ast, bitwise=False)
        except MBABlastDoesNotApplyException as e:
            # this just means the expression is not optimizable
            return (False, [])
        
        
        #print(ast)

        if not isinstance(split_ast, list):
            split_ast = [split_ast]

        #print(split_ast)
        
        
        #print([x  for x in  split_ast])

        # 2. Split terms into coefficient and bitwise expression
        #for ast in split_ast:
    
        coeff_terms = [self._parse_coefficient(ast) for ast in split_ast]

        #print([(cof, x)  for cof, x in  coeff_terms])

        # 3. Turn terms into linear combination of basis vectors

        lcbv = None

        for cof, cast in coeff_terms:
            tt = self._ast_to_truthtable(cast, var_names)
            ct = self._truthtable_to_coefficients(tt, var_amount)

            ctList = []
            for i, v in enumerate(ct):
                if v == 0: continue
                ctList.append(CallNode(CallType.MUL, [I64Node(v), VarNode(self.placeholdersMap[var_amount][i])]))
            
            if len(ctList) == 0: ctList = [I64Node(0)]
            ctExpr = ctList[0]
            for i in range(len(ctList)-1):
                ctExpr = CallNode(CallType.ADD, [ctExpr, ctList[i+1]])

            # Constant Terms have negated coefficient
            if isinstance(cast, I64Node):
                cof = cof * -1

            part = CallNode(CallType.MUL, [I64Node(cof), ctExpr])
            if lcbv == None:
                lcbv = part
            else:
                lcbv = CallNode(CallType.ADD, [lcbv, part])

        if lcbv == None: lcbv = I64Node(0)

        #print(ast_module.unparse(ast_module.parse(ast_to_str(lcbv))))

        # 4. Apply sympy simplification

        sympyVars = {placeholder: sympy.symbols(placeholder) for placeholder in self.placeholdersMap[var_amount]}
        
        #ev = eval(ast_to_str(lcbv), {}, sympyVars)
        ev = map_ast(lcbv, lambda x: sympyVars[x], lambda y: y, {
        CallType.ADD: lambda a, b: a+b,
        CallType.SUB: lambda a, b: a-b,
        CallType.MUL: lambda a, b: a*b,
        CallType.AND: lambda a, b: a&b,
        CallType.OR: lambda a, b: a|b,
        CallType.XOR: lambda a, b: a^b,
        CallType.SHL: lambda a, b: a << b,
        CallType.SHR: lambda a, b: a >> b,
        CallType.NOT: lambda a: ~a,
        CallType.NEG: lambda a: -a,
        })

        # MBA-Blast code implies "**" power can appear?
        ev = str(ev)
        if "**" in ev:
            raise Exception("Power in MBA-Blast simplified code "+ev+" from "+ast)
        

        #print("MBA2:", ev)
        # 5. Replace placeholders with basis expressions

        for placeholder in self.placeholdersMap[var_amount]:
            pB = self.placeholderMapping[var_amount][placeholder]

            # replace basis variable names with current actual variable names
            for i, v in enumerate(var_names):
                pB = pB.replace("_B%02X_" % i, v)

            ev = ev.replace(placeholder, pB)

        #print("MBA2:", ev)
        # 6. Turn back into expression
            
        oexpr = str_to_ast(ev, var_names)

        return (True, [oexpr])

    def failed(self, ast):
        #print("Failed to apply MBA-Blast to", ast)
        pass

    def name(self):
        return "MBABlastEqualityProvider"
