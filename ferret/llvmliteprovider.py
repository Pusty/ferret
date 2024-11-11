from .equalityprovider import EqualityProvider
from .bitvec import *
from .expressionast import *

from egglog import *
from egglog.declarations import *
import re

import llvmlite.ir as ll
import llvmlite.binding as llvm


class LLVMLiteParseException(Exception):
    pass


class LLVMLiteEqualityProvider(EqualityProvider):

    def __init__(self):
        llvm.initialize()
        #llvm.initialize_native_target()
        #llvm.initialize_native_asmprinter() 


    def _ast_to_ir(self, func, var_names, builder, ast):
        return map_ast(ast,
                lambda v: func.args[var_names.index(v)],
                lambda iv: ll.Constant(ll.IntType(64), iv),
                {
                CallType.ADD: lambda a, b: builder.add(a, b),
                CallType.SUB: lambda a, b: builder.sub(a, b),
                CallType.MUL: lambda a, b: builder.mul(a, b),
                CallType.AND: lambda a, b: builder.and_(a, b),
                CallType.OR: lambda a, b: builder.or_(a, b),
                CallType.XOR: lambda a, b: builder.xor(a, b),
                CallType.SHL: lambda a, b: builder.shl(a, b),
                CallType.SHR: lambda a, b: builder.lshr(a, b),
                CallType.NOT: lambda a: builder.not_(a),
                CallType.NEG: lambda a: builder.neg(a)
                }
        )

        
    def expr_to_ir(self, expr: Expr):

        var_names = get_vars_from_expr(expr)
        ast = expr_to_ast(expr)
        #print(ast)
        
        fntype = ll.FunctionType(ll.IntType(64), [ll.IntType(64)]*len(var_names))
        module = ll.Module()
        func = ll.Function(module, fntype, name='__fn')
        bb_entry = func.append_basic_block()

        builder = ll.IRBuilder()
        builder.position_at_end(bb_entry)
        builder.ret(self._ast_to_ir(func, var_names, builder, ast))
        
        return (module, var_names) 
        
    def opt_ir(self, module):
        pmb = llvm.create_pass_manager_builder()
        pmb.opt_level = 3
        pmb.size_level = 2
        pm = llvm.create_module_pass_manager()
        pmb.populate(pm)
        
        llmod = llvm.parse_assembly(str(module))
        if not pm.run(llmod):
          raise NotImplementedError("Failed to optimize")
        
        return llmod

    def parse_ir(self, module, var_names):
        try:
            sm = str(module).split("\n")
            mmap = {}
            
            for i in range(len(var_names)):
                mmap["%."+str(i+1)] = BitVec.var(var_names[i])
                
            infunction = False
            for line in sm:
                line = line.strip()
                if line.endswith(":"): continue
                
                if infunction:
                    if line.startswith("ret "):
                        findRetVar = re.findall(r'ret i64 (%[^ ]+)', line)
                        if len(findRetVar) == 1:
                            return (True, [mmap[findRetVar[0]]])
                        findRetVar = re.findall(r'ret i64 (-?\d+)', line)
                        if len(findRetVar) == 1:
                            return (True, [BitVec(int(findRetVar[0]))])
                        raise LLVMLiteParseException("Malformed ret: "+line) 
                    else:
                        # ignore no signed unwrap flag
                        if " nsw " in line:
                            line = line.replace("nsw ", "")
                        m1 = re.match(r"(%[^ ]+) = ([^ ]+) i64 ((%[^ ]+)|(-?\d+))", line)
                        m2 = re.match(r"(%[^ ]+) = ([^ ]+) i64 ((%[^ ]+)|(-?\d+)), ((%[^ ]+)|(-?\d+))", line)
                        if m2:
                            to = m2.groups()[0]
                            inst = m2.groups()[1]
                            arg0 = m2.groups()[2]
                            arg1 = m2.groups()[5]
                            
                            if arg0.startswith("%"):
                                arg0 = mmap[arg0]
                            else:
                                arg0 = BitVec(int(arg0))
                                
                            if arg1.startswith("%"):
                                arg1 = mmap[arg1]
                            else:
                                arg1 = BitVec(int(arg1))
                                
                            if inst == "add":
                                mmap[to] = arg0 + arg1
                            elif inst == "sub":
                                mmap[to] = arg0 - arg1
                            elif inst == "mul":
                                mmap[to] = arg0 * arg1
                            elif inst == "and":
                                mmap[to] = arg0 & arg1
                            elif inst == "or":
                                mmap[to] = arg0 | arg1
                            elif inst == "xor":
                                mmap[to] = arg0 ^ arg1
                            elif inst == "shl":
                                mmap[to] = arg0 << arg1
                            elif inst == "lshr":
                                mmap[to] = arg0 >> arg1
                            else:
                                raise LLVMLiteParseException("Unknown Instruction in llvmliteprovider", line)
                        elif m1:
                            to = m2.groups()[0]
                            inst = m2.groups()[1]
                            arg0 = m2.groups()[2]
                            if arg0.startswith("%"):
                                arg0 = mmap[arg0]
                            raise LLVMLiteParseException("M1 Inst", line)
                        else:
                            raise LLVMLiteParseException("Unknown instruction in llvmliteprovider: ", line)
                    
                if line.startswith("define "):
                    infunction = True

                if line.startswith("ret "):
                    infunction = False

            raise LLVMLiteParseException("Malformed module in llvmliteprovider")
        except Exception as e:
            print(e)
            print(module)
            return (False, [])

        
        
    def simplify(self, expr: Expr) -> tuple[bool, list[Expr]]:

        #print("IN:", expr_to_str(expr))

        module, var_names = self.expr_to_ir(expr)

        #print(module)

        module = self.opt_ir(module)
        #module = llvm.parse_assembly(str(module))

        #print(module)
        succ, opti = self.parse_ir(module, var_names)

        #if succ:
        #    print("OUT:", expr_to_str(opti[0]))

        """
        target_machine = llvm.Target.from_default_triple().create_target_machine()
        with llvm.create_mcjit_compiler(module, target_machine) as ee:
            ee.finalize_object()
            cfptr = ee.get_function_address("__fn")
            #print(target_machine.emit_assembly(module))
            from ctypes import CFUNCTYPE, c_int, POINTER
            cfunc = CFUNCTYPE(c_int, c_int, c_int)(cfptr)
            res = cfunc(0, 0)
            print("JIT RES AT 0:", res)
        """
                
        return succ, opti
    
    def name(self) -> str:
        return "LLVMLiteEqualityProvider"