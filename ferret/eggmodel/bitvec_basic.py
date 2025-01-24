from .eggmodel import *
from ..expressionast import *
from egglog.bindings import *
import itertools
import json


_rule_commands = None
def _get_bitvec_basic_rules():
    global _rule_commands
    if _rule_commands != None: return _rule_commands
    bitvec_rules = """

(datatype*
  (BitVec
    (BitVec___init__ i64)
    (BitVec_var String)
    (BitVec___add__ BitVec BitVec)
    (BitVec___sub__ BitVec BitVec)
    (BitVec___and__ BitVec BitVec)
    (BitVec___or__ BitVec BitVec)
    (BitVec___xor__ BitVec BitVec)
    (BitVec___lshift__ BitVec BitVec)
    (BitVec___rshift__ BitVec BitVec)
    (BitVec___mul__ BitVec BitVec)
    (BitVec___invert__ BitVec)
    (BitVec___neg__ BitVec)
  )
 )

 ; Integer simplification
(rewrite (BitVec___add__ (BitVec___init__ i) (BitVec___init__ j)) (BitVec___init__ (+ i j)))
(rewrite (BitVec___sub__ (BitVec___init__ i) (BitVec___init__ j)) (BitVec___init__ (- i j)))
(rewrite (BitVec___and__ (BitVec___init__ i) (BitVec___init__ j)) (BitVec___init__ (& i j)))
(rewrite (BitVec___or__ (BitVec___init__ i) (BitVec___init__ j)) (BitVec___init__ (| i j)))
(rewrite (BitVec___xor__ (BitVec___init__ i) (BitVec___init__ j)) (BitVec___init__ (^ i j)))
(rewrite (BitVec___lshift__ (BitVec___init__ i) (BitVec___init__ j)) (BitVec___init__ (<< i j)))
(rewrite (BitVec___rshift__ (BitVec___init__ i) (BitVec___init__ j)) (BitVec___init__ (>> i j)))
(rewrite (BitVec___mul__ (BitVec___init__ i) (BitVec___init__ j)) (BitVec___init__ (* i j)))

; Commutativity
(rewrite (BitVec___mul__ x y) (BitVec___mul__ y x))
(rewrite (BitVec___add__ x y) (BitVec___add__ y x))
(rewrite (BitVec___and__ x y) (BitVec___and__ y x))
(rewrite (BitVec___xor__ x y) (BitVec___xor__ y x))
(rewrite (BitVec___or__ x y) (BitVec___or__ y x))

; Associativity
(rewrite (BitVec___mul__ x (BitVec___mul__ y z)) (BitVec___mul__ (BitVec___mul__ x y) z))
(rewrite (BitVec___mul__ (BitVec___mul__ x y) z) (BitVec___mul__ x (BitVec___mul__ y z)))
(rewrite (BitVec___add__ x (BitVec___add__ y z)) (BitVec___add__ (BitVec___add__ x y) z))
(rewrite (BitVec___add__ (BitVec___add__ x y) z) (BitVec___add__ x (BitVec___add__ y z)))
(rewrite (BitVec___and__ x (BitVec___and__ y z)) (BitVec___and__ (BitVec___and__ x y) z))
(rewrite (BitVec___and__ (BitVec___and__ x y) z) (BitVec___and__ x (BitVec___and__ y z)))
(rewrite (BitVec___xor__ x (BitVec___xor__ y z)) (BitVec___xor__ (BitVec___xor__ x y) z))
(rewrite (BitVec___xor__ (BitVec___xor__ x y) z) (BitVec___xor__ x (BitVec___xor__ y z)))
(rewrite (BitVec___or__ x (BitVec___or__ y z)) (BitVec___or__ (BitVec___or__ x y) z))
(rewrite (BitVec___or__ (BitVec___or__ x y) z) (BitVec___or__ x (BitVec___or__ y z)))

; Normalisation invert
; no change observed?
(rewrite (BitVec___invert__ (BitVec___mul__ x y)) (BitVec___add__ (BitVec___mul__ (BitVec___invert__ x) y) (BitVec___sub__ y (BitVec___init__ 1))))
(rewrite (BitVec___invert__ (BitVec___add__ x y)) (BitVec___add__ (BitVec___invert__ x) (BitVec___add__ (BitVec___invert__ y) (BitVec___init__ 1))))
(rewrite (BitVec___invert__ (BitVec___sub__ x y)) (BitVec___sub__ (BitVec___invert__ x) (BitVec___add__ (BitVec___invert__ y) (BitVec___init__ 1))))
(rewrite (BitVec___invert__ (BitVec___xor__ x y)) (BitVec___or__ (BitVec___and__ x y) (BitVec___invert__ (BitVec___or__ x y))))

; De Morgan
(rewrite (BitVec___invert__ (BitVec___and__ x y)) (BitVec___or__ (BitVec___invert__ x) (BitVec___invert__ y)))
(rewrite (BitVec___invert__ (BitVec___or__ x y)) (BitVec___and__ (BitVec___invert__ x) (BitVec___invert__ y)))

; Normalisation negate
; no observed change?
(rewrite (BitVec___neg__ (BitVec___mul__ x y)) (BitVec___mul__ (BitVec___neg__ x) y))
(rewrite (BitVec___neg__ (BitVec___mul__ x y)) (BitVec___mul__ x (BitVec___neg__ y)))

; Equalities
; seems useful
(rewrite (BitVec___neg__ x) (BitVec___add__ (BitVec___invert__ x) (BitVec___init__ 1)))
(rewrite (BitVec___add__ (BitVec___invert__ x) (BitVec___init__ 1)) (BitVec___neg__ x))
(rewrite (BitVec___add__ x (BitVec___neg__ y)) (BitVec___sub__ x y))
; this rule increases blowup massively
(rewrite (BitVec___sub__ x y) (BitVec___add__ x (BitVec___neg__ y)))

; Inverse distributivity
; seems useful
(rewrite (BitVec___add__ (BitVec___mul__ x y) (BitVec___mul__ x z)) (BitVec___mul__ x (BitVec___add__ y z)))
(rewrite (BitVec___sub__ (BitVec___mul__ x y) (BitVec___mul__ x z)) (BitVec___mul__ x (BitVec___sub__ y z)))

; Collapsing
; no observed change?
(rewrite (BitVec___add__ (BitVec___mul__ x y) y) (BitVec___mul__ (BitVec___add__ x (BitVec___init__ 1)) y))
(rewrite (BitVec___add__ x x) (BitVec___mul__ (BitVec___init__ 2) x))
(rewrite (BitVec___or__ (BitVec___xor__ x y) y) (BitVec___or__ x y))

; Swapping
; no observed change?
(rewrite (BitVec___mul__ x (BitVec___neg__ y)) (BitVec___neg__ (BitVec___mul__ x y)))

; Distributivity
(rewrite (BitVec___mul__ (BitVec___add__ x y) z) (BitVec___add__ (BitVec___mul__ x z) (BitVec___mul__ y z)))
(rewrite (BitVec___mul__ (BitVec___sub__ x y) z) (BitVec___sub__ (BitVec___mul__ x z) (BitVec___mul__ y z)))

; Additional rules
; no observed change?
(rewrite (BitVec___neg__ (BitVec___add__ x y)) (BitVec___add__ (BitVec___neg__ x) (BitVec___neg__ y)))
(rewrite (BitVec___lshift__ (BitVec___and__ x y) z) (BitVec___and__ (BitVec___lshift__ x z) (BitVec___lshift__ y z)))
(rewrite (BitVec___lshift__ (BitVec___rshift__ x z) z) (BitVec___and__ x (BitVec___invert__ (BitVec___sub__ (BitVec___lshift__ (BitVec___init__ 1) z) (BitVec___init__ 1)))))
(rewrite (BitVec___sub__ y (BitVec___and__ (BitVec___invert__ x) y)) (BitVec___and__ x y))
(rewrite (BitVec___add__ (BitVec___lshift__ x z) (BitVec___lshift__ y z)) (BitVec___lshift__ (BitVec___add__ x y) z))
(rewrite (BitVec___lshift__ (BitVec___lshift__ x y) z) (BitVec___lshift__ (BitVec___lshift__ x z) y))
(rewrite (BitVec___sub__ (BitVec___or__ x y) (BitVec___and__ (BitVec___invert__ x) y)) x)

; Trivial identities

(rewrite (BitVec___add__ (BitVec___init__ 0) x) x)
(rewrite (BitVec___sub__ x (BitVec___init__ 0)) x)
(rewrite (BitVec___mul__ x (BitVec___init__ 1)) x)
(rewrite (BitVec___or__ x (BitVec___init__ 0)) x)
(rewrite (BitVec___xor__ x (BitVec___init__ 0)) x)

(rewrite (BitVec___and__ x x) x)
(rewrite (BitVec___or__ x x) x)

(rewrite (BitVec___invert__ (BitVec___invert__ x)) x)
(rewrite (BitVec___neg__ (BitVec___neg__ x)) x)
(rewrite (BitVec___rshift__ x (BitVec___init__ 0)) x)
(rewrite (BitVec___lshift__ x (BitVec___init__ 0)) x)

(rewrite (BitVec___invert__ (BitVec___neg__ x)) (BitVec___sub__ x (BitVec___init__ 1)))

; seems unhelpful?
(rewrite (BitVec___neg__ (BitVec___invert__ x)) (BitVec___add__ x (BitVec___init__ 1)))

;  Null terms
(rewrite (BitVec___and__ x (BitVec___init__ 0)) (BitVec___init__ 0))
(rewrite (BitVec___xor__ x x) (BitVec___init__ 0))
(rewrite (BitVec___sub__ x x) (BitVec___init__ 0))
(rewrite (BitVec___mul__ x (BitVec___init__ 0)) (BitVec___init__ 0))

"""
    _rule_commands = parse_program(bitvec_rules)
    return _rule_commands

class EggBasic(EggModel):

    def __init__(self):
        self.egraph = EGraph(record=False)
        # register basic rules
        self.egraph.run_program(*_get_bitvec_basic_rules())
        self.display_step = []


    def _parse_term_dag(self, termdag, term):
        if isinstance(term, TermVar):
            return term.name
        elif isinstance(term, TermLit):
            return term.value.value
        elif isinstance(term, TermApp):
            f = term.name
            arg = [termdag.nodes[term_id] for term_id in term.args]
            if f == "BitVec___add__":
                return self._parse_term_dag(termdag, arg[0]) + self._parse_term_dag(termdag, arg[1])
            elif f == "BitVec___sub__":
                return self._parse_term_dag(termdag, arg[0]) - self._parse_term_dag(termdag, arg[1])
            elif f == "BitVec___mul__":
                return self._parse_term_dag(termdag, arg[0]) * self._parse_term_dag(termdag, arg[1])
            elif f == "BitVec___and__":
                return self._parse_term_dag(termdag, arg[0]) & self._parse_term_dag(termdag, arg[1])
            elif f == "BitVec___or__":
                return self._parse_term_dag(termdag, arg[0]) | self._parse_term_dag(termdag, arg[1])
            elif f == "BitVec___xor__":
                return self._parse_term_dag(termdag, arg[0]) ^ self._parse_term_dag(termdag, arg[1])
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
        else:
            assert False

    def _ast_to_egg_str(self, ast):
        r = map_ast(ast, 
            lambda var: '(BitVec_var "'+str(var)+'")',
            lambda const: "(BitVec___init__ "+str(const)+")", {
            CallType.ADD: lambda a, b: "(BitVec___add__ "+a+" "+b+")",
            CallType.SUB: lambda a, b: "(BitVec___sub__ "+a+" "+b+")",
            CallType.MUL: lambda a, b: "(BitVec___mul__ "+a+" "+b+")",
            CallType.AND: lambda a, b: "(BitVec___and__ "+a+" "+b+")",
            CallType.OR: lambda a, b: "(BitVec___or__ "+a+" "+b+")",
            CallType.XOR: lambda a, b: "(BitVec___xor__ "+a+" "+b+")",
            CallType.SHL: lambda a, b: "(BitVec___lshift__ "+a+" "+b+")",
            CallType.SHR: lambda a, b: "(BitVec___rshift__ "+a+" "+b+")",
            CallType.NOT: lambda a: "(BitVec___invert__ "+a+")",
            CallType.NEG: lambda a: "(BitVec___neg__ "+a+")"
        })
        return r
    
    def _ast_to_egg(self, ast):
        return map_ast(ast, 
            lambda var: Call(DUMMY_SPAN, "BitVec_var", [Lit(DUMMY_SPAN, String(str(var)))]) ,
            lambda const: Call(DUMMY_SPAN, "BitVec___init__", [Lit(DUMMY_SPAN, Int(const))]), 
            {
            CallType.ADD: lambda a, b: Call(DUMMY_SPAN, "BitVec___add__", [a, b]),
            CallType.SUB: lambda a, b: Call(DUMMY_SPAN, "BitVec___sub__", [a, b]),
            CallType.MUL: lambda a, b: Call(DUMMY_SPAN, "BitVec___mul__", [a, b]),
            CallType.AND: lambda a, b: Call(DUMMY_SPAN, "BitVec___and__", [a, b]),
            CallType.OR: lambda a, b:  Call(DUMMY_SPAN, "BitVec___or__", [a, b]),
            CallType.XOR: lambda a, b: Call(DUMMY_SPAN, "BitVec___xor__", [a, b]),
            CallType.SHL: lambda a, b: Call(DUMMY_SPAN, "BitVec___lshift__", [a, b]),
            CallType.SHR: lambda a, b: Call(DUMMY_SPAN, "BitVec___rshift__", [a, b]),
            CallType.NOT: lambda a: Call(DUMMY_SPAN, "BitVec___invert__", [a]),
            CallType.NEG: lambda a: Call(DUMMY_SPAN, "BitVec___neg__", [a])
        })

    def extract(self, ast, include_cost=False):
        #extract_cmd = "(extract "+self._ast_to_egg_str(ast)+" 0)"
        #self.egraph.run_program(*parse_program(extract_cmd))
        self.egraph.run_program(ActionCommand(Extract(DUMMY_SPAN, self._ast_to_egg(ast), Lit(DUMMY_SPAN, Int(0)))))
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
        #self.egraph.run_program(*parse_program(self._ast_to_egg_str(ast)))
        self.egraph.run_program(ActionCommand(Expr_(DUMMY_SPAN, self._ast_to_egg(ast))))

    def union(self, astA, astB):
        #self.egraph.run_program(*parse_program("(union "+self._ast_to_egg_str(astA)+" "+self._ast_to_egg_str(astB)+")"))
        self.egraph.run_program(ActionCommand(Union(DUMMY_SPAN, self._ast_to_egg(astA), self._ast_to_egg(astB))))

    
    
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
                #r = self.json_to_ast(r)
                # add subexprs to output set
                subexprs.add(r)
                # yield for one layer up in recursion
                yield r

    def json_to_ast(self, subexpr):
        if isinstance(subexpr, Node): return subexpr
        elif isinstance(subexpr, int): return subexpr
        elif isinstance(subexpr, str): return subexpr

        f, arg = subexpr
        if not f[0] == 'B': # doesn't start with BitVec
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
        else:
            raise Exception("Invalid function", f)

    def extract_all_subexprs(self, rootExpr, maxim=-1):
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
            "BitVec___add__": "+",
            "BitVec___sub__": "-",
            "BitVec___mul__": "*",
            "BitVec___and__": "&",
            "BitVec___or__": "|",
            "BitVec___xor__": "^",
            "BitVec___lshift__": "<<",
            "BitVec___rshift__": ">>",
            "BitVec___invert__": "~",
            "BitVec___neg__": "-"
        })
        # inline constants / var names
        pser.inline_leaves()
        self.display_step.append(pser.to_json())
    
    # display the entire graph
    def display(self):
        self.save_display_step()
        from egglog.visualizer_widget import VisualizerWidget 
        VisualizerWidget(egraphs=self.display_step).display_or_open()