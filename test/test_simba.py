from ferret import *


#from .MBABlast_dataset import *
from .MBASolver_dataset import *
#from .MBAObfuscator_dataset import *


print("SiMBA Tests:")



dataset_name, dataset, dataset_groundtruth = parseDataset(1000)[0]


def eval_provider(prov):
    start_value_accum = 0
    end_value_accum = 0
    delta_accum = 0
    groundtruth_accum = 0

    for i in range(len(dataset)):

        expr = dataset[i]
        gexpr = dataset_groundtruth[i]

        success, sexprs = prov.simplify(expr)

        if not success:
            print("Failed to simplify ", expr)
            continue

        sexpr = sexprs[0]

        # QSynth without verification is error prone
        if(not ferret.test_oracle_equality(expr, sexpr)):
            print("[!]", expr, "!=", sexpr)
            continue
                
        egraph = ferret.create_graph()
        egraph.register(expr)
        egraph.register(sexpr)
        egraph.register(gexpr)
        cost_groundtruth = egraph.cost(gexpr)
        cost_before = egraph.cost(expr)
        egraph.union(expr,sexpr)
        cost_after = egraph.cost(expr)

        #print(expr_to_str(out_expr), "=>", expr_to_str(gexpr))

        groundtruth_accum += cost_groundtruth
        start_value_accum += cost_before
        end_value_accum += cost_after

    print("Ground Cost", groundtruth_accum)
    print("Start Cost", start_value_accum)
    print("End Cost", end_value_accum)
    if start_value_accum != 0:
        print("Simplification to", (end_value_accum/start_value_accum)*100, "%")
        print("Groundtruth would be ", (groundtruth_accum/start_value_accum)*100, "%")



sprovr  = SiMBAEqualityProviderReference(checkLinear=True)
eval_provider(sprovr)

sprov  = SiMBAEqualityProvider()
eval_provider(sprov)



x = VarNode("x")
y = VarNode("y")
z = VarNode("z")
#t = VarNode("t")

#print(sprov.simplify(2*~(x|~y) - (x^y) + 2*x))
#expr = 13664254869414482676*((~(x^y)&~t)|(~(x|(y|z))&t)) + 6832127434707241344*((~(y^z)&~t)|((~z&(x^y))&t)) + 15713893099826655077*(((z^~(x|(y&z)))&~t)|(~(~x|(~y|z))&t)) + 10248191152060862011*((~(x^(y&z))&~t)|(((x^y)&~(x^z))&t)) + 3416063717353620669*(((z&(x|y))&~t)|((y^(x|z))&t)) + 10248191152060862013*(((z^~(x|(~y&z)))&~t)|((y^(~x|(~y|z)))&t)) + 1366425486941448269*((~(x&(y&z))&~t)|((x^z)&t)) + 4099276460824344790*(((z&~(x&~y))&~t)|((y^(x&z))&t)) + 6148914691236517211*(((y^(x&(y|z)))&~t)|((~(x|~y)|~(x^(y^z)))&t)) + 12297829382473034411*(((y^~(x&~z))&~t)|((x&(y&z))&t)) + 15030680356355930937*((~(x^(~y&z))&~t)|(((x|~y)&~(y^z))&t)) + 17763531330238827490*((((y&z)|(x&(y|z)))&~t)|(((x&z)|(y&~z))&t)) + 15030680356355930947*(((~x|(y&z))&~t)|(((y&~z)^(x|(y^z)))&t)) + 6832127434707241334*((~(~x&(y|z))&~t)|((z^~(x|(~y&z)))&t)) + 3416063717353620677*((((x&y)^(x^(~y|z)))&~t)|((~(x&~y)&~(y^z))&t)) + 3416063717353620670*(((x|z)&~t)|(((x|y)&~(y^z))&t))


#expr = 1 * ((x | y) & ~(y ^ z)) + 1 * ~(x | (y | z)) - 2 * ~(~x | (y | z)) - 2 * (x & (y & z))
#expr = y * 3 + x * 6 + (y & x) * -8 + ((~x | y) + 1) * 3 + -2 * (y & x) & -2
#expr = -2 ^ x & y #!= -2 + (x & y)
#expr = 11 * ((~y & x) * x) + (-12 + (1 + (~y & x) * -22)) * x + 11 * ((y & x) - x + x) # != -22 * x + 22 * (x & y)
#expr = 4611686018427387902 + ((y | ~x) + 1) * 3
#expr = 4398046511104 & x

expr = ((x ^ -3367252851141315680) & 932861366634999692 ^ 7848617306076253793) * 4147994348508350629 + (x ^ 3367252851141315679 ^ 932861366634999692 ^ 7848617306076253793) * -4147994348508349518 + ((x ^ -3367252851141315680) & -932861366634999693 & 7848617306076253793) * 822011344151721879 + ((~x ^ -3367252851141315680 | 932861366634999692) ^ 7848617306076253793) * -822011344151722990 + ((x ^ -3367252851141315680 | 932861366634999692) ^ 7848617306076253793) * 42327991805736942 + ((~x ^ 3367252851141315679 | 932861366634999692) ^ 7848617306076253793) * -4190322340314086460 + ((x | 3367252851141315679 | 932861366634999692) & -7848617306076253794) * 6589501814189000097 + ((x | 3367252851141315679 | -932861366634999693) & -7848617306076253794) * -1619496121528928700 + ((x ^ 3367252851141315679 | -932861366634999693) & -7848617306076253794) * 6938741743086725350 + (((~x | -3367252851141315680) ^ -932861366634999693) & -7848617306076253794) * -6938741743086723128 + (((x | 3367252851141315679) ^ 932861366634999692) & -7848617306076253794) * 1275021627612252326 + (((x | 3367252851141315679) ^ 932861366634999692) & -7848617306076253794) * 4044223993945542102 + ((x | 3367252851141315679) & -932861366634999693 & -7848617306076253794) * 7373025503284122297 + ((x ^ -3367252851141315680) & -932861366634999693 & -7848617306076253794) * 4932461604715910790 + ((~x | -3367252851141315680) & -932861366634999693 & -7848617306076253794) * 3819113942736363987 + ((~x | -3367252851141315680) & -932861366634999693 & -7848617306076253794) * -5003382736955452224 + (~x & -3367252851141315680 & -932861366634999693 & -7848617306076253794) * 9054473941154563151 + (~x & -3367252851141315680 & -932861366634999693 & -7848617306076253794) * 4472826049008718780

res = sprovr.simplify(expr)
worked, arr = res
if worked:
    refval = arr[0]
    print("Found", ferret.test_oracle_equality(expr, refval), refval)
else:
    print(res)

res = sprov.simplify(expr)
worked, arr = res
if worked:
    refval = arr[0]
    print("Found", ferret.test_oracle_equality(expr, refval), refval)
else:
    print(res)
