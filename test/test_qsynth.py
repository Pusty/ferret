from ferret import *


from .MBABlast_dataset import *


print("QSynth Tests:")




dataset_name, dataset, dataset_groundtruth = parseDataset(600)[0]

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
                
        egraph = EGraph()
        egraph.register(expr)
        egraph.register(sexpr)
        egraph.register(gexpr)
        _, cost_groundtruth = egraph.extract(gexpr, include_cost=True)
        in_expr, cost_before = egraph.extract(expr, include_cost=True)
        egraph.register(union(expr).with_(sexpr))
        out_expr, cost_after = egraph.extract(expr, include_cost=True)

        #print(expr_to_str(out_expr), "=>", expr_to_str(gexpr))

        groundtruth_accum += cost_groundtruth
        start_value_accum += cost_before
        end_value_accum += cost_after

    print("Ground Cost", groundtruth_accum)
    print("Start Cost", start_value_accum)
    print("End Cost", end_value_accum)
    print("Simplification to", (end_value_accum/start_value_accum)*100, "%")
    print("Groundtruth would be ", (groundtruth_accum/start_value_accum)*100, "%")


qprov  = QSynthEqualityProviderReference()
eval_provider(qprov)
# unlock leveldb
del qprov
qprov2 = QSynthEqualityProvider()
eval_provider(qprov2)