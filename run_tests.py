import ferret

from multiprocessing import Pool
import tqdm

import test.MBABlast_dataset as mbablast_dataset
import test.MBAObfuscator_dataset as mbaobf_dataset
import test.MBASolver_dataset as mbasol_dataset
import test.MSiMBA_dataset as msimba_dataset

THREAD_COUNT = 10

def test_eqprovs_sample(sample, equalityprovders):
    dataset_name, expr, gexpr = sample

    # Ground Truth Cost
    cost_groundtruth = ferret.ast_cost(gexpr)

    # Cost of Initial Expression
    cost_before = ferret.ast_cost(expr)

    # Apply (max) 8 runs of rules and equality providers then get cost out
    egg = ferret.create_graph("basic")


    ferret.eclass_simplify(egg, expr, equalityprovders, 3)


    # These settings are for bitvec_basic
    #ferret.iter_simplify(egg, expr, equalityprovders, 5)
    #ferret.all_simplify(egg, expr, equalityprovders, 3)

    #egg.run = lambda x: None
    #ferret.all_simplify(egg, expr, equalityprovders, 3, 10000, 500)

    # These settings are for bitvec_multiset
    #ferret.iter_simplify(egg, expr, equalityprovders, 20, 50000)
    #ferret.all_simplify(egg, expr, equalityprovders, 3, 10000, 10000)

    expr_out = egg.extract(expr)

    cost_after = ferret.ast_cost(expr_out)

    #f = open("eggdump.txt", "w")
    #f.write(egg.egraph.commands())
    #f.close()

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

        if True: #sample_size == 87:
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
    with Pool(THREAD_COUNT) as p:
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
    simba = ferret.SiMBAEqualityProvider()

    boolmin = ferret.BooleanMinifierProvider()

    amount = 250
    dataset = lambda: msimba_dataset.getDataset(amount, skip=0)
    amount = amount * msimba_dataset.getDatasetCount()



    #benchmark_eqprovs(dataset(), [], amount)
    #benchmark_eqprovs(dataset(), [llp], amount)
    #benchmark_eqprovs(dataset(), [mbabp], amount)
    #benchmark_eqprovs(dataset(), [qsynth], amount)
    #benchmark_eqprovs(dataset(), [simba], amount)
    #benchmark_eqprovs(dataset(), [simbaref], amount)

    #benchmark_eqprovs(dataset(), [llp, mbabp], amount)
    #benchmark_eqprovs(dataset(), [qsynth, llp], amount)
    #benchmark_eqprovs(dataset(), [qsynth, mbabp], amount)

    #benchmark_eqprovs(dataset(), [simba, llp], amount)
    #benchmark_eqprovs(dataset(), [simba, qsynth], amount)
    #benchmark_eqprovs(dataset(), [simba, mbabp], amount)

    #benchmark_eqprovs(dataset(), [qsynth, mbabp, llp], amount)
    #benchmark_eqprovs(dataset(), [simba, mbabp, llp], amount)
    #benchmark_eqprovs(dataset(), [qsynth, simba, llp], amount)
    #benchmark_eqprovs(dataset(), [qsynth, mbabp, simba], amount)

    #benchmark_eqprovs(dataset(), [qsynth, mbabp, llp, simbaref], amount)
    #benchmark_eqprovs(dataset(), [qsynth, mbabp, llp, simba], amount)

    benchmark_eqprovs(dataset(), [qsynth, mbabp, llp, simba, boolmin], amount)


    #test_eqprovs(dataset(), [])
    #test_eqprovs(dataset(), [llp])
    #test_eqprovs(dataset(), [mbabp])
    #test_eqprovs(dataset(), [qsynth])
    #test_eqprovs(dataset(), [simba])

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

def run_nastyexpr_test():
    import test.test_nastyexpr


def run_multiset_test_lambda(inpTuple):
    _, expr, gexpr = inpTuple[0]

    #cost_groundtruth = ferret.ast_cost(gexpr)
    #cost_before = ferret.ast_cost(expr)

    eggBasic = ferret.create_graph("basic")
    eggMultiset = ferret.create_graph("multiset")

    for i in range(6):
        eggBasic.simplify(expr)
        eggMultiset.simplify(expr)

    
    #ferret.merge_by_output(eggBasic, expr)
    ferret.merge_by_output(eggMultiset, expr)

    cost_basic = ferret.ast_cost(eggBasic.extract(expr))
    cost_multiset = ferret.ast_cost(eggMultiset.extract(expr))

    nodes_basic = eggBasic.nodecount()
    nodes_multiset = eggMultiset.nodecount()

    if cost_basic < cost_multiset and False:
        print(inpTuple[1], cost_basic," <-> ", cost_multiset, "(", nodes_basic, "/", nodes_multiset,")","#",expr)
        #print(eggMultiset.egraph.commands())
        print(";\t", eggBasic.extract(expr, include_cost=True))
        print(";\t", eggMultiset.extract(expr, include_cost=True))
        #exit(0)
        
    return (cost_basic, nodes_basic, cost_multiset, nodes_multiset)


def run_multiset_test():
    
    amount = 33
    dataset_class = mbasol_dataset
    dataset = [x for x in dataset_class.getDataset(amount, skip=0)]

    
    #with Pool(THREAD_COUNT) as p:
    #    results = list(tqdm.tqdm(p.imap(run_multiset_test_lambda, ([d, i] for i, d in enumerate(dataset))), total=amount*dataset_class.getDatasetCount()))
    if True:
        results = [run_multiset_test_lambda((d, i)) for i, d in enumerate(dataset)]
        sample_size = len(results)

        end_basic_accum = sum((x[0] for x in results))
        nodes_basic_accum = sum((x[1] for x in results))
        end_multiset_accum = sum((x[2] for x in results))
        nodes_multiset_accum = sum((x[3] for x in results))

        print("Basic: ", end_basic_accum/sample_size, "#", nodes_basic_accum/sample_size)
        print("Multiset: ", end_multiset_accum/sample_size, "#", nodes_multiset_accum/sample_size)



if __name__ == '__main__':

    #run_llvmlite_test()
    #run_mbablast_test()
    #run_qsynth_test()
    #run_simba_test()
    #run_multiset_test()

    #run_nastyexpr_test()

    
    run_all_tests()

    """
    import cProfile as profile
    import pstats

    pr = profile.Profile()
    pr.runcall(run_nastyexpr_test)

    st = pstats.Stats(pr)
    st.sort_stats('cumtime')
    st.print_stats() # and other methods like print_callees, print_callers, etc.
    """

