import sys
# needed for SiMBA linearity check
sys.setrecursionlimit(10000)

from ferret import *

a = VarNode("a")
b = VarNode("b")
c = VarNode("c")
d = VarNode("d")
e = VarNode("e")
f = VarNode("f")
g = VarNode("g")
h = VarNode("h")
i = VarNode("i")
l = VarNode("l")
expr = (((((((((((((((((((((((((((((((((((((((((((((((((((((((((((((((((((((((((((((((((((((((((((((((((((((((((((((((((((((((((((((((((((((((((((((((((((((((((((((((((((((((((((((((((((((((((((((a&d)&e)&f)&g)&h)&i)&l)^(((((((b&d)&e)&f)&g)&h)&i)&l))^(((((((c&d)&e)&f)&g)&h)&i)&l))^((((((a&d)&e)&f)&g)&h)&i))^((((((b&d)&e)&f)&g)&h)&i))^((((((c&d)&e)&f)&g)&h)&i))^((((((a&d)&e)&f)&g)&h)&l))^((((((b&d)&e)&f)&g)&h)&l))^((((((c&d)&e)&f)&g)&h)&l))^((((((a&d)&e)&f)&g)&i)&l))^((((((b&d)&e)&f)&g)&i)&l))^((((((c&d)&e)&f)&g)&i)&l))^((((((a&d)&f)&g)&h)&i)&l))^((((((b&d)&f)&g)&h)&i)&l))^((((((c&d)&f)&g)&h)&i)&l))^((((((a&e)&f)&g)&h)&i)&l))^((((((b&e)&f)&g)&h)&i)&l))^((((((c&e)&f)&g)&h)&i)&l))^(((((a&d)&e)&f)&g)&h))^(((((b&d)&e)&f)&g)&h))^(((((c&d)&e)&f)&g)&h))^(((((a&d)&e)&f)&g)&i))^(((((b&d)&e)&f)&g)&i))^(((((c&d)&e)&f)&g)&i))^(((((a&d)&f)&g)&h)&i))^(((((b&d)&f)&g)&h)&i))^(((((c&d)&f)&g)&h)&i))^(((((a&e)&f)&g)&h)&i))^(((((b&e)&f)&g)&h)&i))^(((((c&e)&f)&g)&h)&i))^(((((a&d)&e)&f)&g)&l))^(((((b&d)&e)&f)&g)&l))^(((((c&d)&e)&f)&g)&l))^(((((a&d)&f)&g)&h)&l))^(((((b&d)&f)&g)&h)&l))^(((((c&d)&f)&g)&h)&l))^(((((a&e)&f)&g)&h)&l))^(((((b&e)&f)&g)&h)&l))^(((((c&e)&f)&g)&h)&l))^(((((a&d)&f)&g)&i)&l))^(((((b&d)&f)&g)&i)&l))^(((((c&d)&f)&g)&i)&l))^(((((a&e)&f)&g)&i)&l))^(((((b&e)&f)&g)&i)&l))^(((((c&e)&f)&g)&i)&l))^(((((a&d)&e)&h)&i)&l))^(((((b&d)&e)&h)&i)&l))^(((((c&d)&e)&h)&i)&l))^(((((a&f)&g)&h)&i)&l))^(((((b&f)&g)&h)&i)&l))^(((((c&f)&g)&h)&i)&l))^((((a&d)&e)&f)&g))^((((b&d)&e)&f)&g))^((((c&d)&e)&f)&g))^((((a&d)&f)&g)&h))^((((b&d)&f)&g)&h))^((((c&d)&f)&g)&h))^((((a&e)&f)&g)&h))^((((b&e)&f)&g)&h))^((((c&e)&f)&g)&h))^((((a&d)&f)&g)&i))^((((b&d)&f)&g)&i))^((((c&d)&f)&g)&i))^((((a&e)&f)&g)&i))^((((b&e)&f)&g)&i))^((((c&e)&f)&g)&i))^((((a&d)&e)&h)&i))^((((b&d)&e)&h)&i))^((((c&d)&e)&h)&i))^((((a&f)&g)&h)&i))^((((b&f)&g)&h)&i))^((((c&f)&g)&h)&i))^((((a&d)&f)&g)&l))^((((b&d)&f)&g)&l))^((((c&d)&f)&g)&l))^((((a&e)&f)&g)&l))^((((b&e)&f)&g)&l))^((((c&e)&f)&g)&l))^((((a&d)&e)&h)&l))^((((b&d)&e)&h)&l))^((((c&d)&e)&h)&l))^((((a&f)&g)&h)&l))^((((b&f)&g)&h)&l))^((((c&f)&g)&h)&l))^((((a&d)&e)&i)&l))^((((b&d)&e)&i)&l))^((((c&d)&e)&i)&l))^((((a&f)&g)&i)&l))^((((b&f)&g)&i)&l))^((((c&f)&g)&i)&l))^((((a&d)&h)&i)&l))^((((b&d)&h)&i)&l))^((((c&d)&h)&i)&l))^((((a&e)&h)&i)&l))^((((b&e)&h)&i)&l))^((((c&e)&h)&i)&l))^(((a&d)&f)&g))^(((b&d)&f)&g))^(((c&d)&f)&g))^(((a&e)&f)&g))^(((b&e)&f)&g))^(((c&e)&f)&g))^(((a&d)&e)&h))^(((b&d)&e)&h))^(((c&d)&e)&h))^(((a&f)&g)&h))^(((b&f)&g)&h))^(((c&f)&g)&h))^(((a&d)&e)&i))^(((b&d)&e)&i))^(((c&d)&e)&i))^(((a&f)&g)&i))^(((b&f)&g)&i))^(((c&f)&g)&i))^(((a&d)&h)&i))^(((b&d)&h)&i))^(((c&d)&h)&i))^(((a&e)&h)&i))^(((b&e)&h)&i))^(((c&e)&h)&i))^(((a&d)&e)&l))^(((b&d)&e)&l))^(((c&d)&e)&l))^(((a&f)&g)&l))^(((b&f)&g)&l))^(((c&f)&g)&l))^(((a&d)&h)&l))^(((b&d)&h)&l))^(((c&d)&h)&l))^(((a&e)&h)&l))^(((b&e)&h)&l))^(((c&e)&h)&l))^(((a&d)&i)&l))^(((b&d)&i)&l))^(((c&d)&i)&l))^(((a&e)&i)&l))^(((b&e)&i)&l))^(((c&e)&i)&l))^(((d&h)&i)&l))^((a&d)&e))^((b&d)&e))^((c&d)&e))^((a&f)&g))^((b&f)&g))^((c&f)&g))^((a&d)&h))^((b&d)&h))^((c&d)&h))^((a&e)&h))^((b&e)&h))^((c&e)&h))^((a&d)&i))^((b&d)&i))^((c&d)&i))^((a&e)&i))^((b&e)&i))^((c&e)&i))^((d&h)&i))^((a&d)&l))^((b&d)&l))^((c&d)&l))^((a&e)&l))^((b&e)&l))^((c&e)&l))^((d&h)&l))^((d&i)&l))^((h&i)&l))^(a&d))^(b&d))^(c&d))^(a&e))^(b&e))^(c&e))^(d&h))^(d&i))^(h&i))^(d&l))^(h&l))^(i&l))^d)^h)^i)^l)

print("Input Cost", ast_cost(expr))

# Base cost 1671


llp = LLVMLiteEqualityProvider()
mbabp = MBABlastEqualityProvider()
startQSynthDBServer()
qsynth = QSynthEqualityProvider(dbserver=True)
simbaref = SiMBAEqualityProviderReference()

boolmin = BooleanMinifierProvider()


# cost 37
egg = create_graph("basic")
iter_simplify(egg, expr, [llp, mbabp, qsynth, simbaref, boolmin], 7, 50000)
print("Node Size", egg.nodecount())
expr_out = egg.extract(expr)
print("Output Cost", ast_cost(expr_out))
print(expr_out)



#egg = create_graph("basic")
#all_simplify(egg, expr_out, [llp, mbabp, qsynth, simbaref, boolmin])
#print("Node Size", egg.nodecount())
#expr_out2 = egg.extract(expr_out)
#print("Output Cost", ast_cost(expr_out2))
#print(expr_out2)

#egg = create_graph("basic")
# without increased node size (25000): 1529 (graph size: 73861)
# with increased node size to 100000: 1525 (graph size: 1500874)
#iter_simplify(egg, expr, [llp, mbabp, qsynth, simbaref], 7, 100000)
#print("Node Size", egg.nodecount())
#expr_out = egg.extract(expr)
#print("Output Cost", ast_cost(expr_out))
#print(expr_out)


#egg = create_graph("multiset")
# without increased node size, 3 iterations: 1643 (graph size: 5071)
# without increased node size, 7 iterations: 1643 (graph size: 36510)
#iter_simplify(egg, expr, [llp, mbabp, qsynth, simbaref], 3)
#print("Node Size", egg.nodecount())
#expr_out = egg.extract(expr)
#print("Output Cost", ast_cost(expr_out))


# without increased node size, 3 iterations: 1619 (graph size: 16008)
#egg = create_graph("basic")
#ferret.all_simplify(egg, expr, [llp, mbabp, qsynth, simbaref], 3)
#print("Node Size", egg.nodecount())
#expr_out = egg.extract(expr)
#print("Output Cost", ast_cost(expr_out))

# no improvement at all...
#egg = create_graph("multiset")
#ferret.all_simplify(egg, expr, [llp, mbabp, qsynth, simbaref], 5, 50000, 50000)
#print("Node Size", egg.nodecount())
#expr_out = egg.extract(expr)
#print("Output Cost", ast_cost(expr_out))
#print(expr_out)


# Doesn't help, probably because of subexpr limit
#merge_by_output(egg, expr)
#expr_out = egg.extract(expr)
#print("Output Cost", ast_cost(expr_out))
#print(expr_out)


#egg = create_graph("multiset")
#iter_simplify(egg, expr, [], 20, 50000)
#expr_out = egg.extract(expr)
#print("Output Cost", ast_cost(expr_out))



stopQSynthDBServer()