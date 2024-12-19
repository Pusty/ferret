from .equalityprovider import *
import random

from .eggmodel.eggmodel import EggImpl, EggModel, get_eggmodel_impl

# Project Root

def create_graph(model=None) -> EggModel:
    if model == None: # probably depreciate this
        egg = EggImpl()
    else:
        egg = get_eggmodel_impl(model)()
    return egg

def apply_eqprov(egg: EggModel, eqprov: EqualityProvider, ast: Node):
    success, sasts = eqprov.simplify(ast)
    if success:
        for sast in sasts: 
            egg.union(ast, sast)
            assert_oracle_equality(ast, sast)
    else:
        eqprov.failed(ast)

    
def iter_simplify(egg: EggModel, ast: Node, eqprovs: list[EqualityProvider]=[], inner_max: int=20, max_nodes: int=25000):
    init_cost = egg.cost(ast)

    for eqprov in eqprovs:
        apply_eqprov(egg, eqprov, ast)

    last_amount_nodes = 0
    last_cost = egg.cost(ast)

    for i in range(inner_max):
        
        ast, last_cost = egg.simplify(ast)

        for eqprov in eqprovs:
            apply_eqprov(egg, eqprov, ast)
 
        last_cost = egg.cost(ast)

        #print("====================")
        #print(egg.egraph.commands())
        #print("====================")

        amount_nodes = egg.nodecount()
        #print(amount_nodes)
        
        # probably explodes
        if amount_nodes > max_nodes: break
        # saturated
        if last_amount_nodes == amount_nodes: break
        last_amount_nodes = amount_nodes



    return init_cost, last_cost

def all_simplify(egg: EggModel, ast: Node, eqprovs: list[EqualityProvider]=[], inner_max: int=5, max_nodes: int=500, max_subexpr: int=250):

    init_cost = egg.cost(ast)


    already = set()
    processed = 0
    last_amount_nodes = 0

    for i in range(inner_max):

        if len(eqprovs) > 0:
            options = []
            for subexpr in egg.extract_all_subexprs(ast, 100000):
                uid = hash(subexpr)
                if uid in already: continue
                already.add(uid)
                options.append(subexpr)
            
            # limit the amount of (new) subexpressions to process
            # TODO: If this stays, seed this to make it deterministic
            # Ideally we wouldn't want to limit this at all, but
            # the amount of connection explodes fast
            if max_subexpr != -1 and len(options) >= max_subexpr:
                import random
                random.shuffle(options)
                options = options[:max_subexpr]

            for option in options:
                for eqprov in eqprovs:
                    apply_eqprov(egg, eqprov, egg.json_to_ast(option))

            processed += len(options)
            #print("Procecced ",len(options),"new subexpressions out of ", len(already), "( last node count: ",last_amount_nodes,")")
        egg.run(1)
        amount_nodes = egg.nodecount()
        # probably explodes
        if amount_nodes > max_nodes or processed > max_nodes*2: break
        # saturated
        if last_amount_nodes == amount_nodes: break
        last_amount_nodes = amount_nodes

    #egg.display()

    last_cost = egg.cost(ast)
    return init_cost, last_cost

def test_oracle_equality(astA: Node, astB: Node, N=10, doAssert=False):
    varsA = get_vars_from_ast(astA)
    varsB = get_vars_from_ast(astB)
    varsAB = set(varsA) | set(varsB)
    varMap = {}
    for i in range(N):
        for v in varsAB:
            varMap[v] = random.randint(0, 0xffffffffffffffff)

        evalA = eval_ast(astA, varMap)
        evalB = eval_ast(astB, varMap)
        if doAssert:
            assert evalA  == evalB , astA + " != " + astB +" for "+str(varMap)+" resulting in "+str((evalA, evalB))
        else:
            if evalA != evalB: return False
    return True
    
def assert_oracle_equality(astA: Node, astB: Node, N=10):
    return test_oracle_equality(astA, astB, N=N, doAssert=True)
