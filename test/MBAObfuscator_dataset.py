import os
import csv
from ferret import VarNode, str_to_ast


# ground.linear.nonpoly.txt, ground.linear.poly.txt

ground_linear_nonpoly = []
ground_linear_nonpoly_groundtruth = []

ground_linear_poly = []
ground_linear_poly_groundtruth = []


def parseDataset(maximum=-1):
    if len(ground_linear_nonpoly) != 0: return [("ground_linear_nonpoly", ground_linear_nonpoly, ground_linear_nonpoly_groundtruth), ("ground_linear_poly", ground_linear_poly, ground_linear_poly_groundtruth)]
    PROJECT_PATH = os.getcwd()
    DATASET_PATH = os.path.join(
        PROJECT_PATH,"thirdparty", "MBA-Obfuscator", "samples"
    )

    var_dict = {}
    for v in ["x","y","z","t"]:
        var_dict[v] = VarNode(v)

    with open(os.path.join(DATASET_PATH, "ground.linear.nonpoly.txt"), newline='') as csvfile:
        spamreader = csv.reader(csvfile, delimiter=',')
        i = 0
        for row in spamreader:
            if row[0].startswith("#"): continue
            ground_linear_nonpoly.append(str_to_ast(row[2], var_dict))
            ground_linear_nonpoly_groundtruth.append(str_to_ast(row[1], var_dict))
            i += 1
            if maximum != -1 and i >= maximum: break

    with open(os.path.join(DATASET_PATH, "ground.linear.poly.txt"), newline='') as csvfile:
        spamreader = csv.reader(csvfile, delimiter=',')
        i = 0
        for row in spamreader:
            if row[0].startswith("#"): continue
            ground_linear_poly.append(str_to_ast(row[2], var_dict))
            ground_linear_poly_groundtruth.append(str_to_ast(row[1], var_dict))
            i += 1
            if maximum != -1 and i >= maximum: break

    print("MBA-Obfuscator Dataset parsed")
    return [("ground_linear_nonpoly", ground_linear_nonpoly, ground_linear_nonpoly_groundtruth), ("ground_linear_poly", ground_linear_poly, ground_linear_poly_groundtruth)]

def getDataset(maximum=-1, skip=0):
    PROJECT_PATH = os.getcwd()
    DATASET_PATH = os.path.join(
        PROJECT_PATH,"thirdparty", "MBA-Obfuscator", "samples"
    )

    var_dict = {}
    for v in ["x","y","z","t"]:
        var_dict[v] = VarNode(v)
        
    datasetNames = ["ground_linear_nonpoly", "ground_linear_poly"]
    for datasetName in datasetNames:
        with open(os.path.join(DATASET_PATH, datasetName+".txt"), newline='') as csvfile:
            spamreader = csv.reader(csvfile, delimiter=',')
            i = 0
            for row in spamreader:
                if row[0].startswith("#"): continue
                if i >= skip: yield (datasetName, str_to_ast(row[2], var_dict), str_to_ast(row[1], var_dict))
                i += 1
                if maximum != -1 and i >= maximum: break