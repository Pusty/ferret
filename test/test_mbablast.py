from ferret import *

# the problem with the mbablast impl is that it's very fragile
# and that it basically only works with the mbablast dataset...
from .MBABlast_dataset import *


print("MBA-Blast Tests:")



mbablastprov = MBABlastEqualityProviderReference()
mbablastprov2 = MBABlastEqualityProvider()

dataset_name, dataset, dataset_groundtruth = parseDataset(100)[0]

#dataset = [((BitVec.var("x") & BitVec.var("y")) - (BitVec.var("y") + BitVec.var("x"))) * 11 ]


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
            exit(1)

        sexpr = sexprs[0]
        ferret.assert_oracle_equality(expr, sexpr)
                
        egraph = ferret.create_graph()
        egraph.register(expr)
        egraph.register(sexpr)
        egraph.register(gexpr)
        cost_groundtruth = egraph.cost(gexpr)
        cost_before = egraph.cost(expr)
        egraph.union(expr, sexpr)
        cost_after = egraph.cost(expr)

        groundtruth_accum += cost_groundtruth
        start_value_accum += cost_before
        end_value_accum += cost_after

    print("Ground Cost", groundtruth_accum)
    print("Start Cost", start_value_accum)
    print("End Cost", end_value_accum)
    print("Simplification to", (end_value_accum/start_value_accum)*100, "%")
    print("Groundtruth would be ", (groundtruth_accum/start_value_accum)*100, "%")

eval_provider(mbablastprov)
eval_provider(mbablastprov2)