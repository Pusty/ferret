import ferret
import test
import egglog

from multiprocessing import Pool
import tqdm

import test.MBABlast_dataset as mbaobf_dataset


def test_eqprovs_sample(sample, equalityprovders):
    dataset_name, expr, gexpr = sample

    # Ground Truth Cost
    egraph = egglog.EGraph()
    egraph.register(gexpr)
    _, cost_groundtruth = egraph.extract(gexpr, include_cost=True)

    # Cost of Initial Expression
    egraph.register(expr)
    _, cost_before = egraph.extract(expr, include_cost=True)

    # Apply (max) 8 runs of rules and equality providers then get cost out
    egg = ferret.create_graph()


    #ferret.iter_simplify(egg, expr, equalityprovders, 4)
    ferret.all_simplify(egg, expr, equalityprovders, 3)


    expr_out, cost_after = egg.extract(expr, include_cost=True)

    # Verify expressions through testing random values
    ferret.assert_oracle_equality(gexpr, expr_out)
    return (cost_groundtruth, cost_before, cost_after)


def test_eqprovs(dataset_generator, equalityprovders):
    print("EqProvs: ", ','.join([eqprov.name() for eqprov in equalityprovders]))
    cur_dataset = None

    for sample in dataset_generator:
        dataset_name, expr, gexpr = sample
        if cur_dataset != dataset_name:
            if cur_dataset != None:
                print("\t", "Ground Cost", groundtruth_accum)
                print("\t", "Start Cost", start_value_accum)
                print("\t", "End Cost", end_value_accum)
                print("\t", "Simplification to", (end_value_accum/start_value_accum)*100, "%")
                print("\t", "Groundtruth would be ", (groundtruth_accum/start_value_accum)*100, "%")
            print("\t", "Dataset: ", dataset_name)
            groundtruth_accum = 0
            start_value_accum = 0
            end_value_accum = 0
            cur_dataset = dataset_name
            i = 0
        cost_groundtruth, cost_before, cost_after = test_eqprovs_sample(sample, equalityprovders)
        groundtruth_accum += cost_groundtruth
        start_value_accum += cost_before
        end_value_accum += cost_after
        i += 1

    print("\t", "Ground Cost", groundtruth_accum)
    print("\t", "Start Cost", start_value_accum)
    print("\t", "End Cost", end_value_accum)
    print("\t", "Simplification to", (end_value_accum/start_value_accum)*100, "%")
    print("\t", "Groundtruth would be ", (groundtruth_accum/start_value_accum)*100, "%")


def test_eqprovs_sample_wrapper(tupleThingy):
    return test_eqprovs_sample(tupleThingy[0], tupleThingy[1])

def benchmark_eqprovs(dataset_generator, equalityprovders, totalsamples=-1):
    print("EqProvs: ", ','.join([eqprov.name() for eqprov in equalityprovders]))
    with Pool(16) as p:
        results = list(tqdm.tqdm(p.imap(test_eqprovs_sample_wrapper, ([d, equalityprovders] for d in dataset_generator)), total=totalsamples))

        sample_size = len(results)
        groundtruth_accum = sum((x[0] for x in results))
        start_value_accum = sum((x[1] for x in results))
        end_value_accum = sum((x[2] for x in results))

        ab_avrg = sum(((x[2]/x[1]) for x in results)) / sample_size

        print("\t", "Average Ground Cost", (groundtruth_accum/sample_size))
        print("\t", "Average Before Cost", (start_value_accum/sample_size))
        print("\t", "Average After  Cost", (end_value_accum/sample_size))
        print("\t", "A/B (%)", (ab_avrg)*100, "%")

def run_all_tests():
    llp = ferret.LLVMLiteEqualityProvider()
    mbabp = ferret.MBABlastEqualityProvider()

    ferret.startQSynthDBServer()
    qsynth = ferret.QSynthEqualityProvider(dbserver=True)


    simbaref = ferret.SiMBAEqualityProviderReference()

    amount = 10
    dataset = lambda: mbaobf_dataset.getDataset(amount, skip=0)




    benchmark_eqprovs(dataset(), [], amount)
    benchmark_eqprovs(dataset(), [llp], amount)
    benchmark_eqprovs(dataset(), [mbabp], amount)
    benchmark_eqprovs(dataset(), [qsynth], amount)
    benchmark_eqprovs(dataset(), [simbaref], amount)

    """
    benchmark_eqprovs(dataset(), [llp, mbabp], amount)
    benchmark_eqprovs(dataset(), [qsynth, llp], amount)
    benchmark_eqprovs(dataset(), [qsynth, mbabp], amount)

    benchmark_eqprovs(dataset(), [simbaref, llp], amount)
    benchmark_eqprovs(dataset(), [simbaref, qsynth], amount)
    benchmark_eqprovs(dataset(), [simbaref, mbabp], amount)

    benchmark_eqprovs(dataset(), [qsynth, mbabp, llp], amount)
    benchmark_eqprovs(dataset(), [simbaref, mbabp, llp], amount)
    benchmark_eqprovs(dataset(), [qsynth, simbaref, llp], amount)
    benchmark_eqprovs(dataset(), [qsynth, mbabp, simbaref], amount)

    benchmark_eqprovs(dataset(), [qsynth, mbabp, llp, simbaref], amount)
    """


    #test_eqprovs(dataset(), [])
    #test_eqprovs(dataset(), [llp])
    #test_eqprovs(dataset(), [mbabp])
    #test_eqprovs(dataset(), [llp, mbabp])

    #test_eqprovs(dataset(), [qsynth])
    #test_eqprovs(dataset(), [llp, qsynth])
    #test_eqprovs(dataset(), [mbabp, qsynth])
    #test_eqprovs(dataset(), [llp, mbabp, qsynth])

    ferret.stopQSynthDBServer()

def run_llvmlite_test():
    import test.test_llvmlite

def run_mbablast_test():
    import test.test_mbablast

def run_qsynth_test():
    import test.test_qsynth

def run_simba_test():
    import test.test_simba

#run_llvmlite_test()
#run_mbablast_test()
#run_qsynth_test()
#run_simba_test()

#run_all_tests()


import cProfile as profile
import pstats

pr = profile.Profile()
pr.runcall(run_all_tests)

st = pstats.Stats(pr)
st.sort_stats('cumtime')
st.print_stats() # and other methods like print_callees, print_callers, etc.
