from egglog import *
from egglog.declarations import *
from egglog.runtime import *
from enum import Enum, EnumMeta


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

class Node():
    def __init__(self, nodeType: NodeType):
        self.type = nodeType
    def __getitem__(self, key):
        return [self.type][key]
    def __repr__(self):
        return self.__str__()    

class VarNode(Node):
    def __init__(self, varname: str):
        self.type = NodeType.VAR
        self.value = varname
    def __getitem__(self, key):
        return [self.type, self.value][key]
    def __str__(self):
        return str(self.value)

class I64Node(Node):
    def __init__(self, value: int):
        self.type = NodeType.I64
        self.value = value
    def __getitem__(self, key):
        return [self.type, self.value][key]
    def __str__(self):
        return str(self.value)

class CallNode(Node):
    def __init__(self, callType: CallType, nodes: list[Node]):
        self.type = NodeType.CALL
        self.value = callType
        self.children = nodes
    def __getitem__(self, key):
        return [self.type, self.value, self.children][key]
    def __str__(self):
        nodes = []
        for arg in self.children:
            nodes.append(str(arg))
        if self.value == CallType.ADD:
            return nodes[0]+"+"+nodes[1]
        elif self.value == CallType.SUB:
            return nodes[0]+"-"+nodes[1]
        elif self.value == CallType.MUL:
            return nodes[0]+"*"+nodes[1]
        elif self.value == CallType.AND:
            return nodes[0]+"&"+nodes[1]
        elif self.value == CallType.OR:
            return nodes[0]+"|"+nodes[1]
        elif self.value == CallType.XOR:
            return nodes[0]+"^"+nodes[1]
        elif self.value == CallType.SHL:
            return nodes[0]+"<<"+nodes[1]
        elif self.value == CallType.SHR:
            return nodes[0]+">>"+nodes[1]
        elif self.value == CallType.NOT:
            return "~"+nodes[0]
        elif self.value == CallType.NEG:
            return "-"+nodes[0]
        else:
            raise Exception("Not handled __str__ for "+self.value)


def map_ast(ast, f_var, f_i64, f_call):
    if ast[0] == NodeType.VAR:
        return f_var(ast[1])
    elif ast[0] == NodeType.I64:
        return f_i64(ast[1])
    elif ast[0] == NodeType.CALL:
        nodes = []
        for arg in ast[2]:
            nodes.append(map_ast(arg, f_var, f_i64, f_call))
        if callable(f_call):
            return f_call(ast[1], nodes)
        else:
            return f_call[ast[1]](*nodes)
    else:
        raise Exception("Unknown AST node "+str(ast[0]))


def expr_to_ast(expr):
    if(isinstance(expr, RuntimeExpr)):
        return expr_to_ast(expr_parts(expr))
    elif(isinstance(expr, TypedExprDecl)):
        return expr_to_ast(expr.expr)
    elif(isinstance(expr, CallDecl)):
        if isinstance(expr.callable, ClassMethodRef):
            if expr.callable.method_name == "var":
                return VarNode(expr.args[0].expr.value)
            elif expr.callable.method_name == "__init__":
                return I64Node(expr.args[0].expr.value)
        elif isinstance(expr.callable, InitRef):
            return I64Node(expr.args[0].expr.value)
        elif isinstance(expr.callable, MethodRef):
            pargs = []
            for arg in expr.args:
                pargs.append(expr_to_ast(arg))
            if not expr.callable.method_name in CallType:
                raise Exception("Unsupported AST Call "+str(expr.callable.method_name))
            return CallNode(expr.callable.method_name, pargs)
        else:
            raise Exception("Unknown AST Decl "+str(expr))

    else:
        raise Exception("Unknown AST Expression "+str(expr))


def eval_ast(ast, varMap):
    I64_MASK = 0xffffffffffffffff
    return map_ast(ast, lambda x: (varMap[x]&I64_MASK), lambda y: (y&I64_MASK), {
        CallType.ADD: lambda a, b: (a+b)&I64_MASK,
        CallType.SUB: lambda a, b: (a-b)&I64_MASK,
        CallType.MUL: lambda a, b: (a*b)&I64_MASK,
        CallType.AND: lambda a, b: (a&b),
        CallType.OR: lambda a, b: (a|b),
        CallType.XOR: lambda a, b: (a^b),
        CallType.SHL: lambda a, b: (a<<b)&I64_MASK,
        CallType.SHR: lambda a, b: (a>>b),
        CallType.NOT: lambda a: (~a)&I64_MASK,
        CallType.NEG: lambda a: (-a)&I64_MASK
    })

def ast_to_str(ast):
    return map_ast(ast, lambda x: str(x), lambda y: "("+str(y)+")", lambda ct, n: "("+str(CallNode(ct, n))+")")

def get_vars_from_ast(ast):
    return sorted(set(map_ast(ast, lambda x: [x], lambda y: [], lambda ct, n: sum(n, []))))