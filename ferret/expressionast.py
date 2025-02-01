from enum import Enum, EnumMeta

import ast as ast_module

class ContainsEnumMeta(EnumMeta):  
    def __contains__(cls, item): 
        return item in cls.__members__.values()

class NodeType(str, Enum, metaclass=ContainsEnumMeta):
    VAR = "var"
    I64 = "i64"
    CALL = "call"


class CallType(str, Enum, metaclass=ContainsEnumMeta):
    ADD = "__add__"
    SUB = "__sub__"
    MUL = "__mul__"
    AND = "__and__"
    OR  = "__or__"
    XOR = "__xor__"
    SHL = "__lshift__"
    SHR = "__rshift__"
    NOT = "__invert__"
    NEG = "__neg__"


def builtin_to_ast(o):
    if isinstance(o, Node): return o
    if isinstance(o, int): return I64Node(o)
    if isinstance(o, str): return VarNode(o)
    raise Exception("Unknown ast conversionm for "+str(o)+" of type "+type(o))

class Node():
    def __init__(self, nodeType):
        self.type = nodeType
    def __getitem__(self, key):
        return [self.type][key]
    def __repr__(self):
        return self.__str__()    
    def __eq__(self, other):
        return NotImplementedError()
    def __hash__(self):
        return NotImplementedError()
    
    
    def __add__(self, other):
        return CallNode(CallType.ADD, [builtin_to_ast(self), builtin_to_ast(other)])
    def __radd__(self, other):
        return CallNode(CallType.ADD, [builtin_to_ast(other), builtin_to_ast(self)])
    def __sub__(self, other):
        return CallNode(CallType.SUB, [builtin_to_ast(self), builtin_to_ast(other)])
    def __rsub__(self, other):
        return CallNode(CallType.SUB, [builtin_to_ast(other), builtin_to_ast(self)])
    def __mul__(self, other):
        return CallNode(CallType.MUL, [builtin_to_ast(self), builtin_to_ast(other)])
    def __rmul__(self, other):
        return CallNode(CallType.MUL, [builtin_to_ast(other), builtin_to_ast(self)])
    def __and__(self, other):
        return CallNode(CallType.AND, [builtin_to_ast(self), builtin_to_ast(other)])
    def __rand__(self, other):
        return CallNode(CallType.AND, [builtin_to_ast(other), builtin_to_ast(self)])
    def __or__(self, other):
        return CallNode(CallType.OR, [builtin_to_ast(self), builtin_to_ast(other)])
    def __ror__(self, other):
        return CallNode(CallType.OR, [builtin_to_ast(other), builtin_to_ast(self)])
    def __xor__(self, other):
        return CallNode(CallType.XOR, [builtin_to_ast(self), builtin_to_ast(other)])
    def __rxor__(self, other):
        return CallNode(CallType.XOR, [builtin_to_ast(other), builtin_to_ast(self)])
    def __lshift__(self, other):
        return CallNode(CallType.SHL, [builtin_to_ast(self), builtin_to_ast(other)])
    def __rlshift__(self, other):
        return CallNode(CallType.SHL, [builtin_to_ast(other), builtin_to_ast(self)])
    def __rshift__(self, other):
        return CallNode(CallType.SHR, [builtin_to_ast(self), builtin_to_ast(other)])
    def __rrshift__(self, other):
        return CallNode(CallType.SHR, [builtin_to_ast(other), builtin_to_ast(self)])
    def __invert__(self):
        return CallNode(CallType.NOT, [builtin_to_ast(self)])
    def __neg__(self):
        return CallNode(CallType.NEG, [builtin_to_ast(self)])

class VarNode(Node):
    def __init__(self, varname):
        self.type = NodeType.VAR
        self.value = varname
    def __getitem__(self, key):
        return [self.type, self.value][key]
    def __str__(self):
        return str(self.value)
    def __eq__(self, other):
        if isinstance(other, VarNode):
            return self.type == other.type and self.value == other.value
        return False
    def __hash__(self):
        return hash((self.type, self.value))
    
class I64Node(Node):
    def __init__(self, value):
        self.type = NodeType.I64
        self.value = sign_i64(value)
    def __getitem__(self, key):
        return [self.type, self.value][key]
    def __str__(self):
        return str(self.value)
    def __eq__(self, other):
        if isinstance(other, I64Node):
            return self.type == other.type and self.value == other.value
        return False
    def __hash__(self):
        return hash((self.type, self.value))

from functools import cached_property

class CallNode(Node):
    def __init__(self, callType, nodes):
        self.type = NodeType.CALL
        self.value = callType
        self.children = nodes
    def __getitem__(self, key):
        return [self.type, self.value, self.children][key]
    def __str__(self):
        return ast_module.unparse(ast_module.parse(ast_to_str(self))) 
    def __eq__(self, other):
        if isinstance(other, CallNode):
            return self.type == other.type and self.value == other.value and self.children == other.children
        return False
    

    def __hash__(self):
        return self._cached_hash

    @cached_property
    def _cached_hash(self):
        return  hash((self.type, self.value, hash(tuple(self.children))))

def map_ast(ast, f_var, f_i64, f_call):
    if isinstance(ast, VarNode):
        return f_var(ast.value)
    elif isinstance(ast, I64Node):
        return f_i64(ast.value)
    elif isinstance(ast, CallNode):
        nodes = []
        for arg in ast.children:
            nodes.append(map_ast(arg, f_var, f_i64, f_call))
        if callable(f_call):
            return f_call(ast.value, nodes)
        else:
            return f_call[ast.value](*nodes)
    else:
        raise Exception("Unknown AST node "+str(ast))
    
def map_ast_bfs(ast, f):
    if isinstance(ast, VarNode):
        return ast
    elif isinstance(ast, I64Node):
        return ast
    elif isinstance(ast, CallNode):
        if callable(f):
            r = f(ast.value, ast.children)
        else:
            r = f[ast.value](*ast.children)
        
        if not isinstance(r, Node):
            raise Exception("BFS Results need to be Nodes "+str(r))

        if not isinstance(r, CallNode): # return
            return r
        else: # map children
            return CallNode(r.value, [map_ast_bfs(arg, f) for arg in r.children])
    else:
        raise Exception("Unknown AST node "+str(ast))


def eval_ast(ast, varMap):
    I64_MASK = 0xffffffffffffffff
    return map_ast(ast, lambda x: (varMap[x]&I64_MASK), lambda y: (y&I64_MASK), {
        CallType.ADD: lambda a, b: (a+b)&I64_MASK,
        CallType.SUB: lambda a, b: (a-b)&I64_MASK,
        CallType.MUL: lambda a, b: (a*b)&I64_MASK,
        CallType.AND: lambda a, b: (a&b),
        CallType.OR: lambda a, b: (a|b),
        CallType.XOR: lambda a, b: (a^b),
        CallType.SHL: lambda a, b: (a<<min(b, 64))&I64_MASK,
        CallType.SHR: lambda a, b: (a>>b),
        CallType.NOT: lambda a: (~a)&I64_MASK,
        CallType.NEG: lambda a: (-a)&I64_MASK
    })

def ast_to_str(ast):
    return map_ast(ast, lambda x: str(x), lambda y: "("+str(y)+")", {
        CallType.ADD: lambda a, b: "("+a+"+"+b+")",
        CallType.SUB: lambda a, b: "("+a+"-"+b+")",
        CallType.MUL: lambda a, b: "("+a+"*"+b+")",
        CallType.AND: lambda a, b: "("+a+"&"+b+")",
        CallType.OR: lambda a, b: "("+a+"|"+b+")",
        CallType.XOR: lambda a, b: "("+a+"^"+b+")",
        CallType.SHL: lambda a, b: "("+a+"<<"+b+")",
        CallType.SHR: lambda a, b: "("+a+">>"+b+")",
        CallType.NOT: lambda a: "(~"+a+")",
        CallType.NEG: lambda a: "(-"+a+")"
    })


def get_vars_from_ast(ast):
    return sorted(set(map_ast(ast, lambda x: [x], lambda y: [], lambda ct, n: sum(n, []))))

def ast_cost(ast):
    return map_ast(ast, lambda x: 1, lambda y: 1, lambda ct, n: sum(n)+1)

def str_to_ast(astStr, varNames):

    if isinstance(varNames, list):
        var_dict = {}
        for var_name in varNames:
            var_dict[var_name] = VarNode(var_name)
    elif isinstance(varNames, dict):
        var_dict = varNames
    else:
        raise Exception("Invalid variables provided ", varNames)

    res = eval(astStr, {}, var_dict)
    if isinstance(res, int):
        res = I64Node(res)
    return res

def sign_i64(value):
    value = value & 0xffffffffffffffff
    if value > 0x7fffffffffffffff:
        value = value-0x10000000000000000
    if value < -0x7fffffffffffffff:
        value = value+0x10000000000000000
    return value

def is_linear(ast):
    IS_CONSTANT = 0
    LINEAR = 1
    NON_LINEAR = 2

    linear_condition = lambda a, b:  \
        IS_CONSTANT if a == IS_CONSTANT and b == IS_CONSTANT else \
        (LINEAR if ((a == LINEAR and b == IS_CONSTANT) or (b == LINEAR and a == IS_CONSTANT) ) else NON_LINEAR)

    val = map_ast(ast, lambda x: LINEAR, lambda y: IS_CONSTANT, {
    CallType.ADD: lambda a, b: max(a, b),
    CallType.SUB: lambda a, b: max(a, b),
    CallType.MUL: lambda a, b: linear_condition(a, b),
    CallType.AND: lambda a, b: max(a, b),
    CallType.OR: lambda a, b: max(a, b),
    CallType.XOR: lambda a, b: max(a, b),
    CallType.SHL: lambda a, b: IS_CONSTANT if a == IS_CONSTANT and b == IS_CONSTANT else (LINEAR if (((a == LINEAR) or (a == IS_CONSTANT)) and b == IS_CONSTANT) else NON_LINEAR),
    CallType.SHR: lambda a, b: NON_LINEAR,
    CallType.NOT: lambda a: a,
    CallType.NEG: lambda a: a,
    })

    return val != NON_LINEAR