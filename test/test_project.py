from ferret import *
from egglog import converter, py_eval
import json

print("General Tests:")

test_stuff()


def iter_simplify(egg, expr):
    egg.push()
    init_cost = cost(egg, expr)
    
    for j in range(1):
        egg.push()
        last_amount_nodes = 0
        for i in range(20):
            expr, last_cost = simplify(egg, expr)
            p = json.loads(egg._egraph.serialize([],
                max_functions=None,
                max_calls_per_function=None,
                include_temporary_functions=False).to_json())
            amount_nodes = len(p["nodes"])
            #print(i, expr, last_cost, amount_nodes)
            #print(i, last_cost, amount_nodes)
            # probably explodes
            if amount_nodes > 25000: break
            #if amount_nodes > 10000: break
            # saturated
            if last_amount_nodes == amount_nodes: break
            last_amount_nodes = amount_nodes
            #if amount_nodes > 100000: break
        egg.pop()
    egg.pop()
    return init_cost, last_cost


egg = create_graph()

w = BitVec.var("w")
x = BitVec.var("x")
y = BitVec.var("y")
z = BitVec.var("z")


testExpressionSet = [
    ~(x+y+(~(x+y+x+y))+-z),
    (x&~y)+(-(~y))+(~x)+(-y),
    -(~y)+(x|~y)+(x|~y)+(x|y)+BitVec(1)+(-(x&y)-(x&y)),
    (~y)+(-(~x))+(~x|y)+(~x|y)+(-(x&y))+BitVec(1),
    (((((((-(x&y)-(x&y)-(x&y)-(x&y))-(x^y))+(~(x|y))+(~(x|y))+(~(x|y))+(~(x|y))+(~(x|y)))-(~(x^y)))-(~y))-(x|~y))-(~x)),
    (-(~((-((-(x*y))+1+1))+1))),
    -(x&y)+(x|y)+(~(x^y))-(~y),
    -2*(~x&y)+(-(~y))+2*(~x)+(-y)+2,
    (x^y)+(x^y)+(x^y)+(~(x|y))+(~(x|y))+(~(x|y))+(~(x|y))-(x&~y)-(x&~y)-(x&~y)-(x&~y)-(~x&y)-(~(x^y))-(x|~y)-(~x)+1+1,
    3*(x&y)-(x|y)-(~(x|y))-2*(~x&y)-(~y)-(x|~y),
    (~y)+(~y)+(~y)+(~y)+(~y)+(~x^y&~z)+(~x^y&~z)+(~x^y&~z)+(~x^y&~z)+(~x^y&~z)+(~x^y&~z)+(~x^y&~z)+(~x^y&~z)+(~x^y&~z)+(~x^y&~z)+(~x^y&~z)-(~x&y|~z)-(~x&y|~z)-(~x&y|~z)-(~x&y|~z)-(~x&y|~z)-(~x&y|~z)+(~x|y&z)+(~x|y&z)+(~x|y&z)+(x|~y|~z)+(~x&y&~z)+(~x&y&~z)-(x&y|z)-(x&y|z)-(x&y|z)-(x&y|z)-(~x&y&z)-(~x&y&z)-(x&y^z)-(x&y^z),
    -x-y-y+(x&y)+(x&y)+(x&y)+(x&y)+(x&y)-(~(x|y))-(x&~y)-(~(x^y))+1,
    5*(~(x^y))+2*(~x)-(~x|y)+2*(~(x&y))-y-(x&y)-(x|y)+1+1,
    3*(x^y)+4*(~(x|y))-4*(x&~y)-(~x&y)-(~(x^y))-(x|~y)-(~x)+1+1,
    (x|~y)+(x|~y)+(x|~y)-(~x)-(~x)+(~(x&y))+(~(x&y))+(~(x&y))+(~(x&y))+(~(x&y))+(~(x&y))-y-(x|y)-(x^y),
    6*(x^y)-2*(~x&y|~z)+5*(x&y|~z)+5*(~x^y&z)-(x^y&~z)+(x^~y|~z)-8*(x|~z)-(~x&y)-(x&~y|z)-(~x|y^z)-(y&z),
    -(~x&y)-(x^y)+(~(x^y))-3*x-2*y,
    -(~y)-(~y)-(~y)+(x|~y)+(x|~y)+(x|~y)+(x|~y)+(x|~y)+(x|~y)+(~x)+(~x)-(~x|y)-x-(x&~y)+1,
    ((x+(-((~(y+2))<<((((~((~(x|2))|0xffffffffffffffff))&0x3f)&0x3f)&0x3f))))-3),
    ((x&((~((-x)^(~((~(x&1))|1))))+1))+y),
    (((~(((-(~((~(x+(-((((~((~x)&((~x)|2)))^(~(x&((~(((~((~(((~(x&2))|x)^(~(((~(x&2))|x)|((-((-(-((~(x&2))|x)))+(-(~(-0xffffffffffffffff)))))+0x1)))))&0x1))&(-((~((~(x&2))|x))&0x1)))&0x1))+(-((~((~(x&2))|x))&0x1))))))^(~((y^(y+0xfffffffffffffffe))&0x1)))+(-y)))))&((~((x+(-((((~((~x)&((~x)|2)))^(~(x&((~(((~((~(((~(x&2))|x)^(~(((~(x&2))|x)|((-((~(x&2))|x))+0xffffffffffffffff)))))&0x1))&(-((~((~(x&2))|x))&0x1)))&0x1))+(-((~((~(x&2))|x))&0x1))))))^(~((y^(y+0xfffffffffffffffe))&0x1)))+(-y))))|2))^2))))+(-z))+0xfffffffffffffffe))+(~(-(0xffffffffffffffff+2))))+0xffffffffffffffff),
    ((((~((-((~x)|(~((~((~((~(-((~x)+1)))|0xffffffffffffffff))|(~((-((~x)+1))|x))))&((~((~((~(-((~x)+1)))|0xffffffffffffffff))|(((~(~((~(-((~x)+1)))|0xffffffffffffffff)))&0xffffffffffffffff)&(~((-((~x)+1))|x)))))|(~(((~(~((~(((-(~((~(-((~x)+1)))|0xffffffffffffffff)))+(~(((-((~x)+1))|x)&(~((((-((~x)+1))|x)+y)&(~(((-((~x)+1))|x)|y)))))))&(~(~(~((((((~x)+1)+((~(1|1))&1))*((y^1)|(~(y&2))))|x)|((x+(-(~((~(x&2))|2))))&(-x))))))))&(~(~((((-(~((~(-((~x)+1)))|0xffffffffffffffff)))+0xffffffffffffffff)^(~((-((~x)+1))|x)))&(~(~((-((~x)+1))|x)))))))))+0xffffffffffffffff)&1)))))))&1))&(x&z))+((y*z)+(-(~((z|(~(z&2)))|(-(~((z|(~(z&2)))|(-((z|(~(z&2)))|1))))))))))^(~((~((y+(~(((-x)+(-((-(x^(~x)))&((-(x^(~x)))|1))))|((~((~(x|1))&1))+1))))&((y+x)^(-((z-x)*((z-x)+(~((z-x)|((z-x)&(((-(z-x))+1)|2))))))))))&(~((y+x)|(z-x)))))),
    ((-(((x&z)+(-((y*(y|(~y)))*z)))^(~((~((((y+x)|(z-x))*(-((((y+x)|(z-x))^(~((y+x)|(z-x))))|((((y+x)|(z-x))^((~(~(((y+x)|(z-x))|(~(((~y)+((-((~(y|(y&(~(y&(~(y&(y|(~(((-y)+1)&2))))))))))+(-y)))+x))|((-((-z)+(x+0xfffffffffffffffe)))+(0xfffffffffffffffe&(0xfffffffffffffffe^(~(~((~(0xfffffffffffffffe|2))&(~((-2)&1)))))))))))))&(~((y+x)|((-(((-z)+(-(~(z+(-(z+1))))))+(x+0xfffffffffffffffe)))+(0xfffffffffffffffe&(0xfffffffffffffffe^(~(0xfffffffffffffffe|2)))))))))&(((~((y+x)|((z+(-((-(~x))+2)))+0x3)))&(~(((y+x)|((z+(-((-(~x))+2)))+0x3))&(-(((y+x)|((z+(-((-(~x))+2)))+0x3))+y)))))+(~((((y+x)|((z+(-((((~x)*((~(((~x)|(~((~((~((~x)&1))&1))|2)))|(~((~x)&1))))+0xffffffffffffffff))+2)|(~((~((((~x)*((~(((((~x)^(~((~((((-((-((~x)&1))+1))+2)*0xffffffffffffffff)&1))|2)))+(-((~((~((~((((-((-((~x)&1))+1))+2)*0xffffffffffffffff)&1))|2))|1))&1)))|(~(-((~((~((((-((-((~x)&1))+1))+2)*0xffffffffffffffff)&1))|2))+1))))|(~((~x)&1))))+0xffffffffffffffff))+2)&y))|1)))))+0x3))|2)|0xffffffffffffffff)))))))|0xffffffffffffffff))|(~(((y+x)|(z-x))*w))))))+(-((~((((x&z)+(-((y*(y|(~y)))*z)))^(~((~((((y+x)|(z-x))*(-(((((y+x)|(z-x))^(~((y+x)|(z-x))))|((((y+x)|(z-x))^(~((y+x)|(z-x))))&(~((y+x)|(z-x)))))|((((y+x)|(z-x))^((~(~(((y+x)|(z-x))|(~(((~y)+((-((~(y|(y&(~(y&((~y)&(~((~y)&(~((~y)|1))))))))))+(-y)))+x))|((-((-z)+((~x)+(-(~((x*2)+0xfffffffffffffffe))))))+(0xfffffffffffffffe&(0xfffffffffffffffe^(~(~((~(0xfffffffffffffffe|2))&(~((-2)&1)))))))))))))&(~((y+x)|((-(((-z)+(-(~(z+(-(z+1))))))+((-(~(((-z)+(-(~(z+(-(z+1))))))&(~((-z)+(-(~(z+(-(z+1))))))))))*(x+0xfffffffffffffffe))))+(0xfffffffffffffffe&(0xfffffffffffffffe^(~(0xfffffffffffffffe|2)))))))))&(((~((y+x)|((z+(-((-(~x))+2)))+0x3)))&(~(((y+x)|((z+(-((-(~x))+2)))+0x3))&(-((((y&(~(x&(~(x|1)))))+x)|((z+(-((-(~x))+2)))+0x3))+y)))))+(~((((y+x)|((z+(-((((~x)*((~(((~x)|(~((~((~((~x)&1))&1))|2)))|(~((~x)&1))))+0xffffffffffffffff))+2)|(~((~((((~x)*((~(((((~x)^(~((~((((-((-((~x)&1))+1))+2)*0xffffffffffffffff)&1))|2)))+(-(~(~((((~((~((~((((-((-((~x)&1))+1))+2)*0xffffffffffffffff)&1))|2))|1))+1)+(-1))&1)))))|(~(-((~((~((((-((-((~x)&1))+1))+2)*0xffffffffffffffff)&1))|2))+1))))|(~((~x)&1))))+0xffffffffffffffff))+2)&y))|1)))))+0x3))|2)|0xffffffffffffffff)))))))|(~(~(((((y+x)|(z-x))*(-(((((y+x)|(z-x))^(~((y+x)|(z-x))))|((((y+x)|(z-x))^(~(((y+x)|(z-x))+(~((((y+x)|(z-x))*2)|0xffffffffffffffff)))))&(~((y+x)|(z-x)))))|((((y+x)|(z-x))^((~(~(((y+x)|(z-x))|(~(((~y)+((-((~(y|(y&(~(y&((~y)&(~((~y)&(~((~y)|1))))))))))+(-y)))+x))|((-((-z)+((~x)+(-(~((x*2)+0xfffffffffffffffe))))))+(0xfffffffffffffffe&(0xfffffffffffffffe^(~(~((~(0xfffffffffffffffe|2))&(~((-2)&1)))))))))))))&(~((y+x)|((-(((-z)+(-(~(z+(-(z+1))))))+((-(~(((-z)+(-(~(z+(-(z+1))))))&(~((-z)+(-(~(z+(-(z+1))))))))))*(x+0xfffffffffffffffe))))+(0xfffffffffffffffe&(0xfffffffffffffffe^(~(0xfffffffffffffffe|2)))))))))&(((~((y+x)|((z+(-((-(~x))+2)))+0x3)))&(~(((y+x)|((z+(-((-(~x))+2)))+0x3))&(-((((y&(~(x&(~(x|1)))))+x)|((z+(-((-(~x))+2)))+0x3))+y)))))+(~((((y+x)|((z+(-((((~x)*((~(((~x)|(~((~((~((~x)&1))&1))|2)))|(~((~x)&1))))+0xffffffffffffffff))+2)|(~((~((((~x)*((~(((((~x)^(~((~((((-((-((~x)&1))+1))+2)*0xffffffffffffffff)&1))|2)))+(-(~(~((((~((~((~((((-((-((~x)&1))+1))+2)*0xffffffffffffffff)&1))|2))|1))+1)+(-1))&1)))))|(~(-((~((~((((-((-((~x)&1))+1))+2)*0xffffffffffffffff)&1))|2))+1))))|(~((~x)&1))))+0xffffffffffffffff))+2)&y))|1)))))+0x3))|2)|0xffffffffffffffff)))))))&(~0xffffffffffffffff))|0xffffffffffffffff)))))|(~(((y+x)|(z-x))*w)))))|0xffffffffffffffff))&2))),
    ((~(x&~x)+~(x&~x))&(-~(x|~y)-~(x|~y)-~(x|~y)))+((~(x&~x)+~(x&~x))&(-~(x|~y)-~(x|~y)-~(x|~y)))+((~(x&~x)+~(x&~x))&~(-~(x|~y)-~(x|~y)-~(x|~y)))+((~(x&~x)+~(x&~x))|(-~(x|~y)-~(x|~y)-~(x|~y)))+((~(x&~x)+~(x&~x))|(-~(x|~y)-~(x|~y)-~(x|~y)))+((~(x&~x)+~(x&~x))|(-~(x|~y)-~(x|~y)-~(x|~y)))-((~(x&~x)+~(x&~x))|~(-~(x|~y)-~(x|~y)-~(x|~y)))-((~(x&~x)+~(x&~x))|~(-~(x|~y)-~(x|~y)-~(x|~y)))-((~(x&~x)+~(x&~x))|~(-~(x|~y)-~(x|~y)-~(x|~y)))+~((~(x&~x)+~(x&~x))|(-~(x|~y)-~(x|~y)-~(x|~y)))+~((~(x&~x)+~(x&~x))|(-~(x|~y)-~(x|~y)-~(x|~y)))+~((~(x&~x)+~(x&~x))|(-~(x|~y)-~(x|~y)-~(x|~y)))-~((~(x&~x)+~(x&~x))|~(-~(x|~y)-~(x|~y)-~(x|~y)))-~((~(x&~x)+~(x&~x))|~(-~(x|~y)-~(x|~y)-~(x|~y)))-(x&y)-(x&y)-(x&y),
    4*(x|(-6*(x&y)-7*(x&~y)+2*x+5*~(x&~x)-5*~(x|y)-4*~(x|~y)))-6*(x^y)+3*(x&~y)-3*(x&(-6*(x&y)-7*(x&~y)+2*x+5*~(x&~x)-5*~(x|y)-4*~(x|~y))),
    (((x|~y))&(~y+~y+~y+~y+~y))+(((x|~y))&(~y+~y+~y+~y+~y))+(((x|~y))&(~y+~y+~y+~y+~y))+(((x|~y))&(~y+~y+~y+~y+~y))+(((x|~y))&(~y+~y+~y+~y+~y))+(((x|~y))&(~y+~y+~y+~y+~y))+(((x|~y))&(~y+~y+~y+~y+~y))+(((x|~y))&(~y+~y+~y+~y+~y))+(((x|~y))&~(~y+~y+~y+~y+~y))+(((x|~y))&~(~y+~y+~y+~y+~y))+(((x|~y))&~(~y+~y+~y+~y+~y))+(((x|~y))&~(~y+~y+~y+~y+~y))+(((x|~y))&~(~y+~y+~y+~y+~y))+(((x|~y))&~(~y+~y+~y+~y+~y))+(((x|~y))&~(~y+~y+~y+~y+~y))+(((x|~y))&~(~y+~y+~y+~y+~y))+(((x|~y))&~(~y+~y+~y+~y+~y))-(((x|~y))|~(~y+~y+~y+~y+~y))-(((x|~y))|~(~y+~y+~y+~y+~y))-(((x|~y))|~(~y+~y+~y+~y+~y))-(((x|~y))|~(~y+~y+~y+~y+~y))-(((x|~y))|~(~y+~y+~y+~y+~y))-(((x|~y))|~(~y+~y+~y+~y+~y))-~(((x|~y))&(~y+~y+~y+~y+~y))-~(((x|~y))&(~y+~y+~y+~y+~y))+~(((x|~y))|(~y+~y+~y+~y+~y))+~(((x|~y))|(~y+~y+~y+~y+~y))+~(((x|~y))|(~y+~y+~y+~y+~y))+~(((x|~y))|(~y+~y+~y+~y+~y))+~(((x|~y))|(~y+~y+~y+~y+~y))+~(((x|~y))|(~y+~y+~y+~y+~y))+~(((x|~y))|(~y+~y+~y+~y+~y))+~(((x|~y))|(~y+~y+~y+~y+~y))+~(((x|~y))|~(~y+~y+~y+~y+~y))+~(((x|~y))|~(~y+~y+~y+~y+~y))+~(((x|~y))|~(~y+~y+~y+~y+~y))-~(x|~y)-(x&~y)-(x&~y)-(x&~y)-(x&~y)-(x&~y)-(x&~y)-(x&y)-(x&y)
]

"""
start_value_accum = 0
end_value_accum = 0
delta_accum = 0

for expr in testExpressionSet:
    init_cost, last_cost = iter_simplify(egg, expr)
    start_value_accum += init_cost
    end_value_accum += last_cost
    delta_accum += (init_cost-last_cost)

print("Start Cost", start_value_accum)
print("End Cost", end_value_accum)
print("Delta Cost", delta_accum)
print("Simplification to", (end_value_accum/start_value_accum)*100, "%")
"""

#print(iter_simplify(egg, (-(~((-((-(x*y))+BitVec(1)+BitVec(1)))+BitVec(1))))))
#print(iter_simplify(egg, ~(x+y+(~(x+y+x+y))+-z)))



#print(iter_simplify(egg, (x&~y)+(-(~y))+(~x)+(-y)))
