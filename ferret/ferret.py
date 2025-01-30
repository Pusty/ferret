from .equalityprovider import *
from .solvers import verify_ast
import random
import hashlib
import array


from .eggmodel.eggmodel import EggImpl, EggModel, get_eggmodel_impl

# Project Root

def create_graph(model=None):
    if model == None: # probably deprecate this
        egg = EggImpl()
    else:
        egg = get_eggmodel_impl(model)()
    return egg

def apply_eqprov(egg, eqprov, ast):
    success, sasts = eqprov.simplify(ast)
    if success:
        for sast in sasts: 
            # don't add more expensive equalities
            if ast_cost(sast) > ast_cost(ast): continue
            egg.union(ast, sast)
            assert_oracle_equality(ast, sast, debug=[eqprov.name()])
    else:
        eqprov.failed(ast)


def _process_subexpr_for_merge(subexpr, inpMappings, classes, classesMin, newly_created):
    outs = []
    vars = get_vars_from_ast(subexpr)

    # run the expression against randomized inputs
    for inpMappingIndex in range(len(inpMappings)):
        mapping = inpMappings[inpMappingIndex]
        for var in vars:
            if var not in mapping:
                mapping[var] = random.randint(0, 0xffffffffffffffff)
        outs.append(eval_ast(subexpr, mapping)&0xffffffffffffffff)
    
    # hash the outputs as a eclass key and add it
    h = hashlib.md5(array.array('Q', outs).tobytes()).digest()
    cost = ast_cost(subexpr)
    
    # if newly_created only add if smaller than existing minimum
    if newly_created and h in classesMin: 
        if classesMin[h][0] <= cost: return

    if not newly_created: # newly created are only relevant if they are the minimal element in the class
        if h not in classes:
            classes[h] = set()
        classes[h].add(subexpr)

    if h in classesMin:
        if classesMin[h][0] > cost:
            classesMin[h] = (cost, subexpr)
    else:
        classesMin[h] = (cost, subexpr)


# Merge subexpressions of a graph (given a root expression) by their output behavior
# Verify correctness using SMT Solver
# Enrich by trying to minimize though combinations (e.g. making new constant combinations)
def merge_by_output(egg, root, enrich=False):
    classes = {}
    classesMin = {}
    bestSubexprs = []
    inpMappings = [{} for i in range(5)]

    # Extract subexpressions
    for subexpr in egg.extract_all_subexprs(root, 100000, best=True):
        subexpr = egg.json_to_ast(subexpr) # convert them (this is computation heavy at scale)
        bestSubexprs.append(subexpr)
        _process_subexpr_for_merge(subexpr, inpMappings, classes, classesMin, False)

    #print("Amount of eclasses", len(bestSubexprs))
    if enrich:
        for i in range(len(bestSubexprs)):
            #print(i, len(bestSubexprs))
            a = bestSubexprs[i]
            for j in range(i, len(bestSubexprs)):
                b = bestSubexprs[j]

                #if not isinstance(a, I64Node) and not isinstance(b, I64Node): continue
                if isinstance(a, I64Node) and isinstance(b, I64Node):
                    _process_subexpr_for_merge(I64Node(a.value+b.value), inpMappings, classes, classesMin, True)
                    _process_subexpr_for_merge(I64Node(a.value-b.value), inpMappings, classes, classesMin, True)
                    _process_subexpr_for_merge(I64Node(a.value*b.value), inpMappings, classes, classesMin, True)
                    _process_subexpr_for_merge(I64Node(a.value&b.value), inpMappings, classes, classesMin, True)
                    _process_subexpr_for_merge(I64Node(a.value|b.value), inpMappings, classes, classesMin, True)
                    _process_subexpr_for_merge(I64Node(a.value^b.value), inpMappings, classes, classesMin, True)
                else:
                    for callType in [CallType.ADD, CallType.MUL, CallType.AND, CallType.OR, CallType.XOR]:
                        _process_subexpr_for_merge(CallNode(callType, [a, b]), inpMappings, classes, classesMin,  True)
            
            if isinstance(a, I64Node):
                    _process_subexpr_for_merge(I64Node(-a.value), inpMappings, classes, classesMin, True)
                    _process_subexpr_for_merge(I64Node(~a.value), inpMappings, classes, classesMin, True)
            else:
                    _process_subexpr_for_merge(CallNode(CallType.NEG, [a]), inpMappings, classes, classesMin, True)
                    _process_subexpr_for_merge(CallNode(CallType.NOT, [a]), inpMappings, classes, classesMin, True)

    # Go through all classes and union them if applicable
    for key in classes:
        # skip unique classes
        if len(classes[key]) == 1 and classesMin[key][1] == next(iter(classes[key])): continue
        # union with minimal element
        min_element = classesMin[key][1]
        for astB in classes[key]:
            if astB == min_element:
                continue # skip minimal to minimal merge
            # verify using SMT solver that things are equal (or at least check there isn't obvious counter example)
            if verify_ast(min_element, astB, {"timeout": 100, "unsafe": True, "precision": 64}):
                egg.union(min_element, astB)

def iter_simplify(egg, ast, eqprovs=[], inner_max=20, max_nodes=25000):
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

def all_simplify(egg, ast, eqprovs=[], inner_max=5, max_nodes=500, max_subexpr=250):

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

def test_oracle_equality(astA, astB, N=10, doAssert=False, debug=[]):
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
            assert evalA == evalB , str(astA) + " != " + str(astB) +" for "+str(varMap)+" resulting in "+str((evalA, evalB))+" # "+str(debug)
        else:
            if evalA != evalB: return False
    return True
    
def assert_oracle_equality(astA, astB, N=10, debug=[]):
    return test_oracle_equality(astA, astB, N=N, doAssert=True, debug=debug)
