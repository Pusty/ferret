from .eggmodel import *
from ..expressionast import *
from egglog.bindings import *
import itertools
import json



class EggMultiset(EggModel):

    def __init__(self):
        self.egraph = EGraph(record=False)
        self.display_step = []
        self.let_cache = {}
        self.let_index = 0
        self.union_cache = set()

        egg_rewrites = """
        (datatype*
        (BitVec
            (BitVec___init__ i64)
            (BitVec_var String)
            (BitVec___sub__ BitVec BitVec)
            (BitVec___lshift__ BitVec BitVec)
            (BitVec___rshift__ BitVec BitVec)
            (BitVec___invert__ BitVec)
            (BitVec___neg__ BitVec)
            (BitVecSet__add__ BitVecMultiSet)
            (BitVecSet__mul__ BitVecMultiSet)
            (BitVecSet__and__ BitVecMultiSet)
            (BitVecSet__xor__ BitVecMultiSet)
            (BitVecSet__or__ BitVecMultiSet)
        )
        (sort BitVecToBitVec (UnstableFn (BitVec) BitVec))
        (sort BitVecMultiSet (MultiSet BitVec))
        )
        """

        # add rules
        commands = parse_program(egg_rewrites)
        self.egraph.run_program(*commands)


        commands = parse_program("""
        ; ~(-x) = x-1
        (rewrite (BitVec___invert__ (BitVec___neg__ x)) (BitVecSet__add__ (multiset-of x (BitVec___neg__ (BitVec___init__ 1)))))
                                 
        ; x-x = 0
        (rewrite (BitVec___sub__ x x) (BitVec___init__ 0))

        ; x-0 = x         
        (rewrite (BitVec___sub__ x (BitVec___init__ 0)) x)
                                 
        ; 0-x = x         
        (rewrite (BitVec___sub__ (BitVec___init__ 0) x) (BitVec___neg__ x))   
                                 
        ; a-b = a + (-b)
        (rewrite (BitVec___sub__ a b) (BitVecSet__add__ (multiset-of a (BitVec___neg__ b))))

        ; ~(~x) = x
        (rewrite (BitVec___invert__ (BitVec___invert__ x)) x)

        ; -(-x) = x
        (rewrite (BitVec___neg__ (BitVec___neg__ x)) x)

        ; x >> 0 = x
        (rewrite (BitVec___rshift__ x (BitVec___init__ 0)) x)

        ; x << 0 = x
        (rewrite (BitVec___lshift__ x (BitVec___init__ 0)) x)

        ; -(~x) = x+1
        ;(rewrite (BitVec___neg__ (BitVec___invert__ x)) (BitVecSet__add__ (multiset-of x (BitVec___init__ 1))))
                                 
        ; x & 0 = 0
        (rule
        (
            (= setv (BitVecSet__and__ set-inner))
            (multiset-contains set-inner (BitVec___init__ 0))
        )
        ((union setv(BitVec___init__ 0)))
        )

        ; x * 0 = 0
        (rule
        (
            (= setv (BitVecSet__mul__ set-inner))
            (multiset-contains set-inner (BitVec___init__ 0))
        )
        ((union setv(BitVec___init__ 0)))
        )
        """)
        self.egraph.run_program(*commands)

        commands = parse_program("""
        ;  -x = (~x + 1)
        (rewrite (BitVec___neg__ x) (BitVecSet__add__ (multiset-of (BitVec___invert__ x) (BitVec___init__ 1))))

        ;  (~x + 1) = -x
        (rule
        (
            (= setv (BitVecSet__add__ set-inner))
            (= num-a (BitVec___invert__ x))
            (multiset-contains set-inner num-a)
            (= without-a (multiset-remove set-inner num-a))
            (= num-b (BitVec___init__ 1))
            (multiset-contains without-a num-b)
            (= without-b (multiset-remove without-a num-b))
        )
        (
            (union setv (BitVecSet__add__ (multiset-insert without-b (BitVec___neg__ x))))
        )
        )               
        """)
        # this sometimes improves results, sometimes makes them worse
        # causes 2x grow in nodes
        #self.egraph.run_program(*commands)




        for operator in ["__add__", "__mul__", "__and__", "__xor__", "__or__"]:
            # This rule is turning nested bitvecsets into one big set
            commands = parse_program(f"""
            (rule 
                (
                    (= setv  (BitVecSet{operator} set-inner))
                    (= setiv (BitVecSet{operator} set-inner-inner)) 
                    (multiset-contains set-inner setiv)
                    (= merge (multiset-sum (multiset-remove set-inner setiv) set-inner-inner))
                )
                (
                    (union setv (BitVecSet{operator} merge))
                    (delete (BitVecSet{operator} set-inner))
                )
            )
            """)
            self.egraph.run_program(*commands)

        for operator, identity in [("__add__", "0"), ("__mul__", "1"), ("__xor__", "0"), ("__or__", "0")]:
            # identities:   x <op> identity = x
            commands = parse_program(f"""
            (rule
            (
                (= setv (BitVecSet{operator} set-inner))
                (= num-a (BitVec___init__ {identity}))
                (multiset-contains set-inner num-a)
                (= without-a (multiset-remove set-inner num-a))
            )
            (
                (union setv (BitVecSet{operator} without-a))
                (delete (BitVecSet{operator} set-inner))
            )
            )
            """)
            self.egraph.run_program(*commands)

        for constructors in ["BitVec___init__ x", "BitVec_var x", 
                            "BitVec___sub__ x y",
                            "BitVec___lshift__ x y", "BitVec___rshift__ x y",
                            "BitVec___invert__ x",  "BitVec___neg__ x",
                            "BitVecSet__add__ x", "BitVecSet__mul__ x", "BitVecSet__and__ x",
                            "BitVecSet__xor__ x", "BitVecSet__or__ x"]:
            # normalisation, pushing negatives to leaves
            commands = parse_program(f"""
            (rule
                (
                    (= setv (BitVec___neg__ (BitVecSet__mul__ set-inner))) 
                    (= num-a ({constructors})) 
                    (multiset-contains set-inner num-a)
                    (= without-a (multiset-remove set-inner num-a))
                )
                (
                    (union setv (BitVecSet__mul__ (multiset-insert without-a (BitVec___neg__ num-a))))
                    ;(delete (BitVec___neg__ (BitVecSet__mul__ set-inner)))
                )
            )
            """)
            # I see no improvement from this as of now (but +30% node growth)
            #self.egraph.run_program(*commands)

        # De Morgan's Law
        commands = parse_program("""              
        ; newer versio needs  constructor here
        ; (constructor tmp-invert-fn (BitVec) BitVec) 
        (function tmp-invert-fn (BitVec) BitVec :unextractable)

        (rule ((= tmp (tmp-invert-fn x)))
            ((union tmp (BitVec___invert__ x))
            (delete (tmp-invert-fn x)))
        )
        ;  ~(a & b & c) <-> (~a | ~b | ~c)                   
        (rule (
                (= outer-term (BitVec___invert__ (BitVecSet__and__ bc)))
                (> (multiset-length bc) 1)
            )
            (
                (union outer-term (BitVecSet__or__  (unstable-multiset-map (unstable-fn "tmp-invert-fn") bc)))
            )
        )
        ;  ~(a | b | c) <-> (~a & ~b & ~c)                   
        (rule (
                (= outer-term (BitVec___invert__ (BitVecSet__or__ bc)))
                (> (multiset-length bc) 1)
            )
            (
                (union outer-term (BitVecSet__and__  (unstable-multiset-map (unstable-fn "tmp-invert-fn") bc)))
            )
        )                   
        """)
        self.egraph.run_program(*commands)



        # Distributivity
        commands = parse_program("""
        ; newer version needs ":no-merge" here
        (function tmp-distributivity-fn (BitVecMultiSet BitVec) BitVec :unextractable)           
        (rule ((= tmp (tmp-distributivity-fn xs x)))
            ((union tmp (BitVecSet__mul__ (multiset-insert xs x)))
            (delete (tmp-distributivity-fn xs x)))
        )              

        (rule
        (
            (= sum (BitVecSet__add__ bc))
            (= product (BitVecSet__mul__ product-inner))
            (multiset-contains product-inner sum)
            (> (multiset-length product-inner) 1)
            (= a (multiset-remove product-inner sum))
        )
        (
            (union product (BitVecSet__add__ (unstable-multiset-map (unstable-fn "tmp-distributivity-fn" a) bc)))
        )
        )
        """)
        self.egraph.run_program(*commands)

        # Inverse Distributivity
        # TODO

        for constructors in ["BitVec___init__ x", "BitVec_var x", 
                            "BitVec___sub__ x y",
                            "BitVec___lshift__ x y", "BitVec___rshift__ x y",
                            "BitVec___invert__ x",  "BitVec___neg__ x",
                            "BitVecSet__add__ x", "BitVecSet__mul__ x", "BitVecSet__and__ x",
                            "BitVecSet__xor__ x", "BitVecSet__or__ x"]:
            # normalisation, pushing negatives to up
            commands = parse_program(f"""
            (rule
                (
                    (= setv (BitVecSet__mul__ set-inner))
                    (= num-a (BitVec___neg__ ({constructors}))) 
                    (multiset-contains set-inner num-a)
                    (= without-a (multiset-remove set-inner num-a))
                )
                (
                    (union setv (BitVec___neg__ (BitVecSet__mul__ (multiset-insert without-a ({constructors})))))
                )
            )
            """)
            self.egraph.run_program(*commands)

        for operator, int_operator in [("__add__", "+"), ("__mul__", "*"), ("__and__", "&"), ("__xor__", "^"), ("__or__", "|")]:
            # rules to simplify 2 constants into 1
            commands = parse_program(f"""
            (rule
            (
                (= setv (BitVecSet{operator} set-inner))
                (= num-a (BitVec___init__ a))
                (multiset-contains set-inner num-a)
                (= without-a (multiset-remove set-inner num-a))
                (= num-b (BitVec___init__ b))
                (multiset-contains without-a num-b)
            )
            (
                (union 
                    (BitVecSet{operator} set-inner)
                    (BitVecSet{operator} (multiset-insert (multiset-remove without-a num-b) (BitVec___init__ ({int_operator} a b))))
                )
                ;(delete (BitVecSet{operator} set-inner))
            )
            )
            """)
            self.egraph.run_program(*commands)

        for operator in ["__add__", "__mul__", "__and__", "__xor__", "__or__"]:
            # rules for 0 elements in a set = 0
            commands = parse_program(f"""
            (rule 
                (
                    (= setv (BitVecSet{operator} set-inner))
                    (= 0 (multiset-length set-inner))
                )
                (
                    (union setv (BitVec___init__ 0))
                    (delete (BitVecSet{operator} set-inner))
                )
                
            )
            """)
            self.egraph.run_program(*commands)

        for operator in ["__add__", "__mul__", "__and__", "__xor__", "__or__"]:
            # rules for 1 element in a set = that element
            commands = parse_program(f"""
            (rule 
                (
                    (= setv (BitVecSet{operator} set-inner))
                    (= 1 (multiset-length set-inner))
                )
                (
                    (union setv (multiset-pick set-inner))
                    (delete (BitVecSet{operator} set-inner))
                )
            )
            """)
            self.egraph.run_program(*commands)


        # Trivial identities (double occurance)

        commands = parse_program("""

        ; x&x = x

        (rule
        (
            (= setv (BitVecSet__and__ set-inner))
            (!= 0 (multiset-length set-inner))
            (= num-a (multiset-pick set-inner))
            (= without-a (multiset-remove set-inner num-a))
            (multiset-contains without-a num-a)
        )
        (
        (union setv (BitVecSet__and__ without-a))
        )
        )

        ; x|x = x

        (rule
        (
            (= setv (BitVecSet__or__ set-inner))
            (!= 0 (multiset-length set-inner))
            (= num-a (multiset-pick set-inner))
            (= without-a (multiset-remove set-inner num-a))
            (multiset-contains without-a num-a)
        )
        (
        (union setv (BitVecSet__or__ without-a))
        )
        )
        ; x^x = 0

        (rule
        (
            (= setv (BitVecSet__xor__ set-inner))
            (!= 0 (multiset-length set-inner))
            (= num-a (multiset-pick set-inner))
            (= without-a (multiset-remove set-inner num-a))
            (multiset-contains without-a num-a)
        )
        (
        (union setv (BitVecSet__xor__ (multiset-remove without-a num-a)))
        )
        )
        """)
        self.egraph.run_program(*commands)



    def _parse_term_dag(self, termdag, term):
        if isinstance(term, TermVar):
            return term.name
        elif isinstance(term, TermLit):
            return term.value.value
        elif isinstance(term, TermApp):
            f = term.name
            arg = [termdag.nodes[term_id] for term_id in term.args]
            if f == "BitVec___sub__":
                return self._parse_term_dag(termdag, arg[0]) - self._parse_term_dag(termdag, arg[1])
            elif f == "BitVec___lshift__":
                return self._parse_term_dag(termdag, arg[0]) << self._parse_term_dag(termdag, arg[1])
            elif f == "BitVec___rshift__":
                return self._parse_term_dag(termdag, arg[0]) >> self._parse_term_dag(termdag, arg[1])
            elif f == "BitVec___invert__":
                return ~self._parse_term_dag(termdag, arg[0])
            elif f == "BitVec___neg__":
                return -self._parse_term_dag(termdag, arg[0])
            elif f == "BitVec___init__":
                return I64Node(self._parse_term_dag(termdag, arg[0]))
            elif f == "BitVec_var":
                return VarNode(self._parse_term_dag(termdag, arg[0]))
            elif f == "multiset-of":
                return [self._parse_term_dag(termdag, a) for a in arg]
            elif f.startswith("BitVecSet"):
                _set = self._parse_term_dag(termdag, arg[0])
                if len(_set) == 0 and f.endswith("__mul__"): return I64Node(1) 
                if len(_set) == 0: return I64Node(0) 
                r = _set[0]
                if f.endswith("__add__"):
                    for startIndex in range(len(_set)):
                        if not (isinstance(_set[startIndex],CallNode) and _set[startIndex].value == CallType.NEG):
                            break
                    r = _set[startIndex] # start with addition to optimize out one neg
                    for i in range(len(_set)):
                        if i == startIndex: continue
                        # simplification for +(-(x)) to -x
                        if isinstance(_set[i],CallNode) and _set[i].value == CallType.NEG:
                            r = r - _set[i].children[0]
                        else:
                            r = r + _set[i]
                elif f.endswith("__mul__"):
                    sign = True
                    for i in range(1, len(_set)):
                        #if isinstance(_set[i],CallNode) and _set[i].value == CallType.NEG:
                        #    sign = not sign
                        r = r * _set[i]
                elif f.endswith("__and__"):
                    for i in range(1, len(_set)):
                        r = r & _set[i]
                elif f.endswith("__xor__"):
                    for i in range(1, len(_set)):
                        r = r ^ _set[i]
                elif f.endswith("__or__"):
                    for i in range(1, len(_set)):
                        r = r | _set[i]
                else:
                    assert False
            else:
                raise Exception("Unknown function "+f)
            return r
        else:
            assert False

    def _ast_to_egg_str(self, ast):
        return map_ast(ast, 
            lambda var: '(BitVec_var "'+str(var)+'")',
            lambda const: "(BitVec___init__ "+str(const)+")", {
            CallType.ADD: lambda a, b: "(BitVecSet__add__ (multiset-of "+a+" "+b+"))",
            CallType.SUB: lambda a, b: "(BitVec___sub__ "+a+" "+b+")",
            CallType.MUL: lambda a, b: "(BitVecSet__mul__ (multiset-of "+a+" "+b+"))",
            CallType.AND: lambda a, b: "(BitVecSet__and__ (multiset-of "+a+" "+b+"))",
            CallType.OR: lambda a, b: "(BitVecSet__or__ (multiset-of "+a+" "+b+"))",
            CallType.XOR: lambda a, b: "(BitVecSet__xor__ (multiset-of "+a+" "+b+"))",
            CallType.SHL: lambda a, b: "(BitVec___lshift__ "+a+" "+b+")",
            CallType.SHR: lambda a, b: "(BitVec___rshift__ "+a+" "+b+")",
            CallType.NOT: lambda a: "(BitVec___invert__ "+a+")",
            CallType.NEG: lambda a: "(BitVec___neg__ "+a+")"
            })
    
    def _ast_to_egg(self, ast):
        return map_ast(ast, 
        lambda var: Call(DUMMY_SPAN, "BitVec_var", [Lit(DUMMY_SPAN, String(str(var)))]) ,
        lambda const: Call(DUMMY_SPAN, "BitVec___init__", [Lit(DUMMY_SPAN, Int(const))]), 
        {
        CallType.ADD: lambda a, b: Call(DUMMY_SPAN, "BitVecSet__add__", [Call(DUMMY_SPAN, "multiset-of",[a, b])]),
        CallType.MUL: lambda a, b: Call(DUMMY_SPAN, "BitVecSet__mul__", [Call(DUMMY_SPAN, "multiset-of",[a, b])]),
        CallType.AND: lambda a, b: Call(DUMMY_SPAN, "BitVecSet__and__", [Call(DUMMY_SPAN, "multiset-of",[a, b])]),
        CallType.OR: lambda a, b:  Call(DUMMY_SPAN, "BitVecSet__or__", [Call(DUMMY_SPAN, "multiset-of",[a, b])]),
        CallType.XOR: lambda a, b: Call(DUMMY_SPAN, "BitVecSet__xor__", [Call(DUMMY_SPAN, "multiset-of", [a, b])]),
        
        CallType.SUB: lambda a, b: Call(DUMMY_SPAN, "BitVec___sub__", [a, b]),
        CallType.SHL: lambda a, b: Call(DUMMY_SPAN, "BitVec___lshift__", [a, b]),
        CallType.SHR: lambda a, b: Call(DUMMY_SPAN, "BitVec___rshift__", [a, b]),
        CallType.NOT: lambda a: Call(DUMMY_SPAN, "BitVec___invert__", [a]),
        CallType.NEG: lambda a: Call(DUMMY_SPAN, "BitVec___neg__", [a])
    })

    def extract(self, ast, include_cost=False):
        #return ast
        if ast not in self.let_cache:
            #extract_cmd = "(extract "+self._ast_to_egg_str(ast)+" 0)"
            #self.egraph.run_program(*parse_program(extract_cmd))
            self.egraph.run_program(ActionCommand(Extract(DUMMY_SPAN, self._ast_to_egg(ast), Lit(DUMMY_SPAN, Int(0)))))
        else:
            self.egraph.run_program(ActionCommand(Extract(DUMMY_SPAN, Var(DUMMY_SPAN, self.let_cache[ast]), Lit(DUMMY_SPAN, Int(0)))))

        report = self.egraph.extract_report()
        cost = report.cost
        term = self._parse_term_dag(report.termdag, report.term)

        if include_cost:
            return (term, cost)
        else:
            return term

    def run(self, rounds):
        #self.egraph.run_program(*parse_program("(run-schedule (repeat "+str(rounds)+" (run)))"))
        self.egraph.run_program(RunSchedule(Sequence(DUMMY_SPAN, [Repeat(DUMMY_SPAN, rounds, Sequence(DUMMY_SPAN, [Run(DUMMY_SPAN, RunConfig('', None))]))])))
    
    def register(self, ast):

        if ast not in self.let_cache:
            letStr = "sol_"+str(self.let_index)
            self.let_cache[ast] = letStr
            self.let_index += 1

            #self.egraph.run_program(*parse_program("(let "+letStr+" "+self._ast_to_egg_str(ast)+")"))
            self.egraph.run_program(ActionCommand(Let(DUMMY_SPAN, letStr, self._ast_to_egg(ast))))

        #self.egraph.run_program(*parse_program(self._ast_to_egg_str(ast)))
        self.egraph.run_program(ActionCommand(Expr_(DUMMY_SPAN, self._ast_to_egg(ast))))

    def union(self, astA, astB):

        if (astA, astB) in self.union_cache or (astB, astA) in self.union_cache: return

        self.union_cache.add((astA, astB))

        if astA in self.let_cache:
            pastA = Var(DUMMY_SPAN, self.let_cache[astA])
        else:
            pastA = self._ast_to_egg(astA)

        if astB in self.let_cache:
            pastB = Var(DUMMY_SPAN, self.let_cache[astB])
        else:
            pastB = self._ast_to_egg(astB)

        if pastA == pastB: return

        #self.egraph.run_program(*parse_program("(union "+self._ast_to_egg_str(astA)+" "+self._ast_to_egg_str(astB)+")"))
        self.egraph.run_program(ActionCommand(Union(DUMMY_SPAN, pastA, pastB)))
    
    
    def nodecount(self):
        pjson = self.egraph.serialize([],
                    max_functions=None,
                    max_calls_per_function=None,
                    include_temporary_functions=False).to_json()
        p = json.loads(pjson)
        return len(p["nodes"])
    

    def _traverse_egraph_nodes(self, nodes, cur, eclasses, nodeclass, seen, subexprs, maxim):
        if cur in seen: return
        if maxim != -1 and len(subexprs) >= maxim: return
        # don't travel the same path twice
        seen = seen | set([cur])
        # for every node in this equivalence class
        for node in eclasses[cur]:
            # all products of child equivalent classes
            for args in itertools.product(*[self._traverse_egraph_nodes(nodes, nodeclass[child], eclasses, nodeclass, seen, subexprs, maxim) for child in nodes[node]["children"]]):
                if maxim != -1 and len(subexprs) >= maxim: return
                r = (nodes[node]["op"], args)
                if r[0] == "tmp-invert-fn" or r[0] == "tmp-distributivity-fn": continue
                #r = self.json_to_ast(r)
                # add subexprs to output set
                subexprs.add(r)
                # yield for one layer up in recursion
                yield r

    def _traverse_egraph_nodes_best(self, nodes, cur, eclasses, nodeclass, seen, best):
        if cur in best:
            yield best[cur][1]
        if cur in seen: 
            return
        # don't calculate best node for eclass twice
        seen.add(cur)
        # for every node in this equivalence class
        for node in eclasses[cur]:
            # all products of child equivalent classes
            for args in itertools.product(*[self._traverse_egraph_nodes_best(nodes, nodeclass[child], eclasses, nodeclass, seen, best) for child in nodes[node]["children"]]):
                r = (nodes[node]["op"], args)
                if r[0] == "tmp-invert-fn" or r[0] == "tmp-distributivity-fn": continue
                if cur in best:
                    cur_best = best[cur][0]
                else:
                    cur_best = 0xffffffffffffffff
                if r[0][0] == "B": 
                    cost = ast_cost(self.json_to_ast(r))
                else: 
                    cost = 0
                if cur_best > cost:
                    best[cur] = (cost, r)
        if cur in best:
            yield best[cur][1]
        return

    def json_to_ast(self, subexpr):
        if isinstance(subexpr, Node): return subexpr
        elif isinstance(subexpr, int): return subexpr
        elif isinstance(subexpr, str): return subexpr

        f, arg = subexpr
        if not f[0] == 'B': # doesn't start with BitVec
            if f == "multiset-of":
                return [self.json_to_ast(a) for a in arg]
            if f[0] == '"' or f[0] == "'": # var
                return f[1:-1]
            else: # or num
                return int(f)
        elif f == "BitVec___add__":
            return self.json_to_ast(arg[0]) + self.json_to_ast(arg[1])
        elif f == "BitVec___sub__":
            return self.json_to_ast(arg[0]) - self.json_to_ast(arg[1])
        elif f == "BitVec___mul__":
            return self.json_to_ast(arg[0]) * self.json_to_ast(arg[1])
        elif f == "BitVec___and__":
            return self.json_to_ast(arg[0]) & self.json_to_ast(arg[1])
        elif f == "BitVec___or__":
            return self.json_to_ast(arg[0]) | self.json_to_ast(arg[1])
        elif f == "BitVec___xor__":
            return self.json_to_ast(arg[0]) ^ self.json_to_ast(arg[1])
        elif f == "BitVec___lshift__":
            return self.json_to_ast(arg[0]) << self.json_to_ast(arg[1])
        elif f == "BitVec___rshift__":
            return self.json_to_ast(arg[0]) >> self.json_to_ast(arg[1])
        elif f == "BitVec___invert__":
            return ~self.json_to_ast(arg[0])
        elif f == "BitVec___neg__":
            return -self.json_to_ast(arg[0])
        elif f == "BitVec___init__":
            return I64Node(self.json_to_ast(arg[0]))
        elif f == "BitVec_var":
            return VarNode(self.json_to_ast(arg[0]))
        elif f.startswith("BitVecSet"):
            _set = self.json_to_ast(arg[0])
            if len(_set) == 0 and f.endswith("__mul__"): return I64Node(1) 
            if len(_set) == 0: return I64Node(0) 
            r = _set[0]
            if f.endswith("__add__"):
                for startIndex in range(len(_set)):
                    if not (isinstance(_set[startIndex],CallNode) and _set[startIndex].value == CallType.NEG):
                        break
                r = _set[startIndex] # start with addition to optimize out one neg
                for i in range(len(_set)):
                    if i == startIndex: continue
                    # simplification for +(-(x)) to -x
                    if isinstance(_set[i],CallNode) and _set[i].value == CallType.NEG:
                        r = r - _set[i].children[0]
                    else:
                        r = r + _set[i]
            elif f.endswith("__mul__"):
                for i in range(1, len(_set)):
                    r = r * _set[i]
            elif f.endswith("__and__"):
                for i in range(1, len(_set)):
                    r = r & _set[i]
            elif f.endswith("__xor__"):
                for i in range(1, len(_set)):
                    r = r ^ _set[i]
            elif f.endswith("__or__"):
                for i in range(1, len(_set)):
                    r = r | _set[i]
            else:
                raise Exception("Invalid function", f)
            return r
        else:
            raise Exception("Invalid function", f)

    def extract_all_subexprs(self, rootExpr, maxim=-1, best=False):
            
            if rootExpr in self.let_cache:
                _root = Var(DUMMY_SPAN, self.let_cache[rootExpr])
            else:
                _root = self._ast_to_egg(rootExpr)

            json_egraph = self.egraph.serialize([_root],
                max_functions=None,
                max_calls_per_function=None,
                include_temporary_functions=False).to_json()
            
            json_egraph = json.loads(json_egraph)

            # start extracting subexpr from here
            root = json_egraph["root_eclasses"][0]
            eclasses = {}
            nodeclass = {}
            for cl in json_egraph["class_data"]:
                eclasses[cl] = set()
                
            for nodeID in json_egraph["nodes"]:
                node = json_egraph["nodes"][nodeID]
                eclasses[node["eclass"]].add(nodeID)
                nodeclass[nodeID]= node["eclass"]
            
            subexprs = set()
            # fill the subexprs set
            if best:
                best_per_class = {}
                seen = set()
                # start by root
                for r in self._traverse_egraph_nodes_best(json_egraph["nodes"], root, eclasses, nodeclass, seen, best_per_class):
                    pass
                # check eclasses not covered
                #seen = set()
                #for eclass in eclasses:
                #    if eclass not in best_per_class:
                #        for r in self._traverse_egraph_nodes_best(json_egraph["nodes"], eclass, eclasses, nodeclass, seen, best_per_class):
                #            pass
                for key in best_per_class:
                    cost, expr = best_per_class[key]
                    subexprs.add(expr)
            else:
                for r in self._traverse_egraph_nodes(json_egraph["nodes"], root, eclasses,nodeclass, set(), subexprs, maxim):
                    pass


            for r in subexprs:
                # skip raw numbers and var names
                if r[0][0] != "B": continue
                #if not isinstance(r, Node): continue
                yield r
                

    # save current graph as a display step
    def save_display_step(self):
        pser = self.egraph.serialize([],
                    max_functions=None,
                    max_calls_per_function=None,
                    include_temporary_functions=False)
        pser.map_ops({
            "BitVec_var": "var",
            "BitVec___init__": "i64",
            "BitVec___sub__": "-",
            "BitVec___lshift__": "<<",
            "BitVec___rshift__": ">>",
            "BitVec___invert__": "~",
            "BitVec___neg__": "-",

            "BitVecSet__add__": "+",
            "BitVecSet__mul__": "*",
            "BitVecSet__xor__": "^",
            "BitVecSet__and__": "&",
            "BitVecSet__or__": "|",
        })
        # inline constants / var names
        pser.inline_leaves()
        self.display_step.append(pser.to_json())
    
    # display the entire graph
    def display(self):
        self.save_display_step()
        from egglog.visualizer_widget import VisualizerWidget 
        VisualizerWidget(egraphs=self.display_step).display_or_open()