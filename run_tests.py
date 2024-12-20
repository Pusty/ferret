import ferret

from multiprocessing import Pool
import tqdm

import test.MBABlast_dataset as mbaobf_dataset


def test_eqprovs_sample(sample, equalityprovders):
    dataset_name, expr, gexpr = sample

    # Ground Truth Cost
    cost_groundtruth = ferret.ast_cost(gexpr)

    # Cost of Initial Expression
    cost_before = ferret.ast_cost(expr)

    # Apply (max) 8 runs of rules and equality providers then get cost out
    egg = ferret.create_graph("basic")


    # These settings are for bitvec_basic
    #ferret.iter_simplify(egg, expr, equalityprovders, 4)
    #ferret.all_simplify(egg, expr, equalityprovders, 3)

    egg.run = lambda x: None
    ferret.all_simplify(egg, expr, equalityprovders, 3, 10000, 500)

    # These settings are for bitvec_multiset
    #ferret.iter_simplify(egg, expr, equalityprovders, 20, 50000)
    #ferret.all_simplify(egg, expr, equalityprovders, 3, 10000, 10000)

    expr_out = egg.extract(expr)

    cost_after = ferret.ast_cost(expr_out)

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
                print("\t", "Average Ground Cost", (groundtruth_accum/sample_size))
                print("\t", "Average Before Cost", (start_value_accum/sample_size))
                print("\t", "Average After  Cost", (end_value_accum/sample_size))
                print("\t", "A/B (%)", (ab_accum/sample_size)*100, "%")
            print("\t", "Dataset: ", dataset_name)
            groundtruth_accum = 0
            start_value_accum = 0
            end_value_accum = 0
            ab_accum = 0
            cur_dataset = dataset_name
            sample_size = 0
        cost_groundtruth, cost_before, cost_after = test_eqprovs_sample(sample, equalityprovders)
        groundtruth_accum += cost_groundtruth
        start_value_accum += cost_before
        end_value_accum   += cost_after
        ab_accum          += (cost_after / start_value_accum)
        sample_size += 1

        print("\t", "Average Ground Cost", (groundtruth_accum/sample_size))
        print("\t", "Average Before Cost", (start_value_accum/sample_size))
        print("\t", "Average After  Cost", (end_value_accum/sample_size))
        print("\t", "A/B (%)", (ab_accum/sample_size)*100, "%")


def test_eqprovs_sample_wrapper(tupleThingy):
    return test_eqprovs_sample(tupleThingy[0], tupleThingy[1])

def benchmark_eqprovs(dataset_generator, equalityprovders, totalsamples=-1):
    print("EqProvs: ", ','.join([eqprov.name() for eqprov in equalityprovders]))
    with Pool(10) as p:
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

    amount = 100
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
    #test_eqprovs(dataset(), [qsynth])
    #test_eqprovs(dataset(), [simbaref])

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
