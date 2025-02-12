import ferret
import ferret.solvers

import test.MBABlast_dataset as mbablast_dataset
import test.MBAObfuscator_dataset as mbaobf_dataset
import test.MBASolver_dataset as mbasol_dataset
import random

import argparse
import time
import psutil
import os
import tracemalloc


def applyStrategy(name, egg, expr, eqprovs, options):
    if name == "iterative":
        inner_max = options.get("inner_max", 5)
        max_nodes = options.get("max_nodes", 25000)
        ferret.iter_simplify(egg, expr, eqprovs, inner_max, max_nodes)
    elif name == "all-subsets":
        inner_max = options.get("inner_max", 3)
        max_nodes = options.get("max_nodes", 500)
        max_subexpr = options.get("max_subexpr", 250)
        ferret.all_simplify(egg, expr, eqprovs, inner_max, max_nodes, max_subexpr)
    elif name == "best-subsets":
        inner_max = options.get("inner_max", 5)
        max_nodes = options.get("max_nodes", 25000)
        ferret.eclass_simplify(egg, expr, eqprovs, inner_max, max_nodes)
    else:
        raise Exception("Unknown Strategy '"+str(name)+"'")

def getDataset(name):
    amount = -1
    skip = 0
    if name == "mba-blast": return mbablast_dataset.getDataset(amount, skip=skip)
    elif name == "mba-obfuscator": return mbaobf_dataset.getDataset(amount, skip=skip)
    elif name == "mba-solver": return mbasol_dataset.getDataset(amount, skip=skip)
    else:
        raise Exception("Unknown Dataset '"+str(name)+"'")

def getEqProv(name):
    if name == "llvm": return ferret.LLVMLiteEqualityProvider()
    elif name == "mba-blast": return ferret.MBABlastEqualityProvider()
    elif name == "qsynth": return ferret.QSynthEqualityProvider()
    elif name == "simba": return ferret.SiMBAEqualityProvider()
    elif name == "boolmin": return ferret.BooleanMinifierProvider()
    else:
        raise Exception("Unknown Equality Provider '"+str(name)+"'")
    
def apply(expr, args, strategy_options):
    egg = ferret.create_graph(args.mode)
    if args.norun:
        egg.run = lambda x: None

    applyStrategy(args.strategy, egg, expr, eqprovs, strategy_options)
    if args.merge:
        ferret.merge_by_output(egg, expr, True)
    return egg.extract(expr)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog="run_eval")
    parser.add_argument("--seed", help="Random seed", type=int)
    parser.add_argument("--eqprov", nargs='*', help="Equality Providers", type=str, default=[], choices={"llvm", "mba-blast", "qsynth", "simba", "boolmin"})
    parser.add_argument("--dataset", help="Datasets", type=str, choices={"mba-blast", "mba-obfuscator", "mba-solver"}, required=True)
    parser.add_argument("--strategy", help="Datasets", type=str, choices={"iterative", "all-subsets", "best-subsets"}, required=True)

    # options for strategy
    parser.add_argument("--inner_max", type=int)
    parser.add_argument("--max_nodes", type=int)
    parser.add_argument("--max_subexpr", type=int)


    parser.add_argument("--smt",  help="SMT Solver", type=str, default="default", choices={"z3", "bitwuzla", "default"})
    parser.add_argument("--mode",  help="E-Graph Mode of Operation", type=str, default="basic", choices={"basic", "multiset"})
    # unsafe vs safe
    parser.add_argument("--safe",  help="Strict SMT Verification",action='store_true')
    parser.add_argument("--merge",  help="Merge Same I/O at the end",action='store_true')
    parser.add_argument("--norun",  help="Disable E-Graph Rule application",action='store_true')

    args = parser.parse_args()

    if args.seed != None:
        random.seed(args.seed)


    if args.smt != "default":
        ferret.solvers.solver_selection_overwrite(args.smt)
    
    if args.safe:
        ferret.solvers.solver_safety_overwrite(args.safe)

    strategy_options = {}
    if args.inner_max != None:
        strategy_options["inner_max"] = args.inner_max
    if args.max_nodes != None:
        strategy_options["max_nodes"] = args.max_nodes
    if args.max_subexpr != None:
        strategy_options["max_subexpr"] = args.max_subexpr

    dataset = getDataset(args.dataset)
    eqprovs = [getEqProv(eqprovname) for eqprovname in set(args.eqprov)]

    amount = 0
    index = 0
    cost_groundtruth_accum = 0
    cost_before_accum = 0
    cost_after_accum = 0
    time_accum = 0
    amount_failed = 0

    print(args)
    print("###################################################")
    for sample in dataset:
        try:
            
            dataset_name, expr, gexpr = sample

            cost_groundtruth = ferret.ast_cost(gexpr)
            cost_before = ferret.ast_cost(expr)

            mem_before = psutil.Process(os.getpid()).memory_info().rss
            time_before = time.process_time_ns()
            tracemalloc.start()
            expr_out = apply(expr, args, strategy_options)
            current_memory, peak_memory = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            time_elapsed = time.process_time_ns()-time_before
            mem_after = psutil.Process(os.getpid()).memory_info().rss

            cost_after = ferret.ast_cost(expr_out)
            ferret.assert_oracle_equality(gexpr, expr_out)

            amount += 1
            cost_groundtruth_accum += cost_groundtruth
            cost_before_accum += cost_before
            cost_after_accum += cost_after
            time_accum += time_elapsed
            print(index, ",","cost_groundtruth", ",", cost_groundtruth)
            print(index, ",","cost_before", ",", cost_before)
            print(index, ",","cost_after", ",", cost_after)
            print(index, ",","time", ",", time_elapsed)
            print(index, ",", "psutil_memory", ",", mem_before, ",", mem_after)
            print(index, ",", "tracemalloc", ",", current_memory, ",", peak_memory)
        except ferret.FerretOracleEqualityException as e:
            amount_failed += 1
            print(index, ",", "failed")
            print(index, ",", "error_log", ",", str(e))
        index += 1
    print("###################################################")
    print("amount", ",", amount)
    print("amount_failed", ",", amount_failed)
    print("cost_groundtruth_accum", ",", cost_groundtruth_accum)
    print("cost_before_accum", ",", cost_before_accum)
    print("cost_after_accum", ",", cost_after_accum)
    print("time_accum", ",", time_accum)