from .expressionast import *

solver_functions = {}

def verify_ast(astA, astB, options):
    if "bitwuzla" in solver_functions:
        return solver_functions["bitwuzla"](astA, astB, options)
    if "z3" in solver_functions:
        return solver_functions["z3"](astA, astB, options)
    raise Exception("No solver installed (either z3 or bitwuzla)")


try:
    import z3

    def _ast_to_z3(bits, z3_vars, ast):
        return map_ast(ast, lambda x: z3_vars[x], lambda y: z3.BitVecVal(y, bits), {
        CallType.ADD: lambda a, b: a+b,
        CallType.SUB: lambda a, b: a-b,
        CallType.MUL: lambda a, b: a*b,
        CallType.AND: lambda a, b: a&b,
        CallType.OR: lambda a, b: a|b,
        CallType.XOR: lambda a, b: a^b,
        CallType.SHL: lambda a, b: a << b,
        CallType.SHR: lambda a, b: z3.LShR(a, b), # logical
        CallType.NOT: lambda a: ~a,
        CallType.NEG: lambda a: -a,
        })

    def verify_ast_z3(astA, astB, options):

        precision = options.get("precision", 64)
        unsafe = options.get("unsafe", True)
        timeout = options.get("timeout", 250)

        var_names = get_vars_from_ast(astA) + get_vars_from_ast(astB)
        z3_vars = {x:z3.BitVec(x, precision) for x in var_names}


        z3A = _ast_to_z3(precision, z3_vars, astA)
        z3B = _ast_to_z3(precision, z3_vars, astB)

        solver = z3.Solver()
        solver.set('timeout', timeout)
        solver.add(z3A != z3B)

        result = solver.check()
        if unsafe:
            return result in [z3.unsat, z3.unknown]
        else:
            return result in [z3.unsat]

    solver_functions["z3"] = verify_ast_z3
except ImportError as e:
    pass

try:
    import bitwuzla
    import time

    def _ast_to_bitwuzla(tm, sortbv, bw_vars, ast, precision):
        return map_ast(ast, lambda x: bw_vars[x], lambda y: tm.mk_bv_value(sortbv, y&((1<<precision)-1)), {
        CallType.ADD: lambda a, b: tm.mk_term(bitwuzla.Kind.BV_ADD, [a, b]),
        CallType.SUB: lambda a, b: tm.mk_term(bitwuzla.Kind.BV_SUB, [a, b]),
        CallType.MUL: lambda a, b: tm.mk_term(bitwuzla.Kind.BV_MUL, [a, b]),
        CallType.AND: lambda a, b: tm.mk_term(bitwuzla.Kind.BV_AND, [a, b]),
        CallType.OR: lambda a, b: tm.mk_term(bitwuzla.Kind.BV_OR, [a, b]),
        CallType.XOR: lambda a, b: tm.mk_term(bitwuzla.Kind.BV_XOR, [a, b]),
        CallType.SHL: lambda a, b: tm.mk_term(bitwuzla.Kind.BV_SHL, [a, b]),
        CallType.SHR: lambda a, b: tm.mk_term(bitwuzla.Kind.BV_SHR, [a, b]), # logical
        CallType.NOT: lambda a: tm.mk_term(bitwuzla.Kind.BV_NOT, [a]),
        CallType.NEG: lambda a: tm.mk_term(bitwuzla.Kind.BV_NEG, [a]),
        })

    class BitwuzlaTimeTerminator:
        def __init__(self, time_limit):
            self.start_time = time.time()
            self.time_limit = time_limit

        def __call__(self):
            return (time.time() - self.start_time)*1000 > self.time_limit

    def verify_ast_bitwuzla(astA, astB, options):

        precision = options.get("precision", 64)
        unsafe = options.get("unsafe", True)
        timeout = options.get("timeout", 250)

        tm = bitwuzla.TermManager()
        options = bitwuzla.Options()
        options.set(bitwuzla.Option.PRODUCE_MODELS, False)
        options.set(bitwuzla.Option.ABSTRACTION, True)

        bw = bitwuzla.Bitwuzla(tm, options)

        sortbv = tm.mk_bv_sort(precision)

        var_names = get_vars_from_ast(astA) + get_vars_from_ast(astB)

        bw_vars = {x:tm.mk_const(sortbv, x) for x in var_names}

        bwA = _ast_to_bitwuzla(tm, sortbv, bw_vars, astA, precision)
        bwB = _ast_to_bitwuzla(tm, sortbv, bw_vars, astB, precision)

        bw.assert_formula(tm.mk_term(bitwuzla.Kind.DISTINCT, [bwA, bwB]))
        bw.configure_terminator(BitwuzlaTimeTerminator(timeout))

        result = bw.check_sat()
        if unsafe:
            return result in [bitwuzla.Result.UNSAT, bitwuzla.Result.UNKNOWN]
        else:
            return result in [bitwuzla.Result.UNSAT]
        
    solver_functions["bitwuzla"] = verify_ast_bitwuzla
except ImportError as e:
    pass 