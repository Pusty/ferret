import random
import argparse
import time
import psutil
import os
import tracemalloc

import sys
import os.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir, "test")))

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir, os.path.pardir, "GAMBA", "src")))

# GAMBA import
import simplify_general

import ferret

def getDataset(name):
    amount = -1
    skip = 0
    if name == "mba-blast": 
        import MBABlast_dataset as mbablast_dataset
        return mbablast_dataset.getDataset(amount, skip=skip)
    elif name == "mba-obfuscator":
        import MBAObfuscator_dataset as mbaobf_dataset
        return mbaobf_dataset.getDataset(amount, skip=skip)
    elif name == "mba-solver": 
        import MBASolver_dataset as mbasol_dataset
        return mbasol_dataset.getDataset(amount, skip=skip)
    elif name == "msimba":
        import MSiMBA_dataset as msimba_dataset
        return msimba_dataset.getDataset(amount, skip=skip)
    else:
        raise Exception("Unknown Dataset '"+str(name)+"'")



if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog="run_gamba_eval")
    parser.add_argument("--seed", help="Random seed", type=int)
    parser.add_argument("--dataset", help="Datasets", type=str, choices={"mba-blast", "mba-obfuscator", "mba-solver", "msimba"}, required=True)

    # only process index % nth == 0
    parser.add_argument("--only_nth", type=int)
    args = parser.parse_args()

    if args.seed != None:
        random.seed(args.seed)


    dataset = getDataset(args.dataset)
   
    amount = 0
    index = 0
    cost_groundtruth_accum = 0
    cost_before_accum = 0
    cost_after_accum = 0
    time_accum = 0
    amount_failed = 0

    exitFunc = sys.exit
    def exit_overwrite(x):
        if isinstance(x, (int, float, complex)) and not isinstance(x, bool):
            exitFunc(x)
        else:
            print(x)

    sys.exit = exit_overwrite
    print(args, flush=True)
    print("###################################################", flush=True)
    for sample in dataset:
        # skip if not n-th element
        if args.only_nth != None and args.only_nth > 0:
            if index % args.only_nth != 0:
                index = index + 1
                continue
        try:
            
            dataset_name, expr, gexpr = sample

            cost_groundtruth = ferret.ast_cost(gexpr)
            cost_before = ferret.ast_cost(expr)

            mem_before = psutil.Process(os.getpid()).memory_info().rss
            time_before = time.process_time_ns()
            tracemalloc.start()

            # Apply General GAMBA without verification
            simpl = simplify_general.simplify_mba(str(expr), 64, False, False, None)

            current_memory, peak_memory = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            time_elapsed = time.process_time_ns()-time_before
            mem_after = psutil.Process(os.getpid()).memory_info().rss

            expr_out = ferret.str_to_ast(simpl, ferret.get_vars_from_ast(expr))
            cost_after = ferret.ast_cost(expr_out)
            ferret.assert_oracle_equality(gexpr, expr_out)

            amount += 1
            cost_groundtruth_accum += cost_groundtruth
            cost_before_accum += cost_before
            cost_after_accum += cost_after
            time_accum += time_elapsed
            print(index, ",","cost_groundtruth", ",", cost_groundtruth, flush=True)
            print(index, ",","cost_before", ",", cost_before, flush=True)
            print(index, ",","cost_after", ",", cost_after, flush=True)
            print(index, ",","time", ",", time_elapsed, flush=True)
            print(index, ",", "psutil_memory", ",", mem_before, ",", mem_after, flush=True)
            print(index, ",", "tracemalloc", ",", current_memory, ",", peak_memory, flush=True)
        except Exception as e:
            amount_failed += 1
            print(index, ",", "failed", flush=True)
            print(index, ",", "error_log", ",", repr(e), flush=True)
        index += 1
    print("###################################################", flush=True)
    print("amount", ",", amount, flush=True)
    print("amount_failed", ",", amount_failed, flush=True)
    print("cost_groundtruth_accum", ",", cost_groundtruth_accum, flush=True)
    print("cost_before_accum", ",", cost_before_accum, flush=True)
    print("cost_after_accum", ",", cost_after_accum, flush=True)
    print("time_accum", ",", time_accum, flush=True)