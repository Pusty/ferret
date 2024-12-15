import os
import csv
from ferret import VarNode, str_to_ast


# pldi_dataset_linear_MBA.txt, pldi_dataset_nonpoly_MBA.txt, pldi_dataset_poly_MBA.txt

pldi_dataset_linear_MBA = []
pldi_dataset_linear_MBA_groundtruth = []

pldi_dataset_nonpoly_MBA = []
pldi_dataset_nonpoly_MBA_groundtruth = []

pldi_dataset_poly_MBA = []
pldi_dataset_poly_MBA_groundtruth = []

def parseDataset(maximum=-1):
    if len(pldi_dataset_linear_MBA) != 0: return [("pldi_dataset_linear_MBA", pldi_dataset_linear_MBA, pldi_dataset_linear_MBA_groundtruth), ("pldi_dataset_nonpoly_MBA", pldi_dataset_nonpoly_MBA, pldi_dataset_nonpoly_MBA_groundtruth), ("pldi_dataset_poly_MBA", pldi_dataset_poly_MBA, pldi_dataset_poly_MBA_groundtruth)]
    PROJECT_PATH = os.getcwd()
    DATASET_PATH = os.path.join(
        PROJECT_PATH,"thirdparty", "MBA-Solver", "full-dataset"
    )

    var_dict = {}
    for v in ["a","b","x","y","z","t"]:
        var_dict[v] = VarNode(v)

    with open(os.path.join(DATASET_PATH, "pldi_dataset_linear_MBA.txt"), newline='') as csvfile:
        spamreader = csv.reader(csvfile, delimiter=',')
        i = 0
        for row in spamreader:
            if row[0].startswith("#"): continue
            pldi_dataset_linear_MBA.append(str_to_ast(row[0], var_dict))
            pldi_dataset_linear_MBA_groundtruth.append(str_to_ast(row[1], var_dict))
            i += 1
            if maximum != -1 and i >= maximum: break

    with open(os.path.join(DATASET_PATH, "pldi_dataset_nonpoly_MBA.txt"), newline='') as csvfile:
        spamreader = csv.reader(csvfile, delimiter=',')
        i = 0
        for row in spamreader:
            if row[0].startswith("#"): continue
            pldi_dataset_nonpoly_MBA.append(str_to_ast(row[0], var_dict))
            pldi_dataset_nonpoly_MBA_groundtruth.append(str_to_ast(row[1], var_dict))
            i += 1
            if maximum != -1 and i >= maximum: break

    with open(os.path.join(DATASET_PATH, "pldi_dataset_poly_MBA.txt"), newline='') as csvfile:
        spamreader = csv.reader(csvfile, delimiter=',')
        i = 0
        for row in spamreader:
            if row[0].startswith("#"): continue
            pldi_dataset_poly_MBA.append(str_to_ast(row[0], var_dict))
            pldi_dataset_poly_MBA_groundtruth.append(str_to_ast(row[1], var_dict))
            i += 1
            if maximum != -1 and i >= maximum: break

    print("MBA-Solver Dataset parsed")
    return [("pldi_dataset_linear_MBA", pldi_dataset_linear_MBA, pldi_dataset_linear_MBA_groundtruth), ("pldi_dataset_nonpoly_MBA", pldi_dataset_nonpoly_MBA, pldi_dataset_nonpoly_MBA_groundtruth), ("pldi_dataset_poly_MBA", pldi_dataset_poly_MBA, pldi_dataset_poly_MBA_groundtruth)]


def getDataset(maximum=-1, skip=0):
    PROJECT_PATH = os.getcwd()
    DATASET_PATH = os.path.join(
        PROJECT_PATH,"thirdparty", "MBA-Solver", "full-dataset"
    )

    var_dict = {}
    for v in ["a","b","x","y","z","t"]:
        var_dict[v] = VarNode(v)


    datasetNames = ["pldi_dataset_linear_MBA", "pldi_dataset_nonpoly_MBA", "pldi_dataset_poly_MBA"]
    for datasetName in datasetNames:
        with open(os.path.join(DATASET_PATH, datasetName+".txt"), newline='') as csvfile:
            spamreader = csv.reader(csvfile, delimiter=',')
            i = 0
            for row in spamreader:
                if row[0].startswith("#"): continue
                if i >= skip: yield (datasetName,  str_to_ast(row[0], var_dict), str_to_ast(row[1], var_dict))
                i += 1
                if maximum != -1 and i >= maximum: break