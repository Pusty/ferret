import os
import csv
from ferret import VarNode, str_to_ast



# dataset2_64bit.txt

dataset2_64bit = []
dataset2_64bit_groundtruth = []


def parseDataset(maximum=-1):
    if len(dataset2_64bit) != 0: return [("dataset2_64bit", dataset2_64bit, dataset2_64bit_groundtruth)]
    PROJECT_PATH = os.getcwd()
    DATASET_PATH = os.path.join(
        PROJECT_PATH,"thirdparty", "MBA-Blast", "dataset"
    )

    var_dict = {}
    for v in ["a","b","c", "d", "e", "f", "x","y","z","t"]:
        var_dict[v] = VarNode(v)

    with open(os.path.join(DATASET_PATH, "dataset2_64bit.txt"), newline='') as csvfile:
        spamreader = csv.reader(csvfile, delimiter=',')
        i = 0
        for row in spamreader:
            if row[0].startswith("#"): continue
            dataset2_64bit.append(str_to_ast(row[0], var_dict))
            dataset2_64bit_groundtruth.append(str_to_ast(row[1], var_dict))
            i += 1
            if maximum != -1 and i >= maximum: break

    print("MBA-Blast Dataset parsed")
    return [("dataset2_64bit", dataset2_64bit, dataset2_64bit_groundtruth)]


def getDataset(maximum=-1, skip=0):
    PROJECT_PATH = os.getcwd()
    DATASET_PATH = os.path.join(
        PROJECT_PATH,"thirdparty", "MBA-Blast", "dataset"
    )

    var_dict = {}
    for v in ["a","b","c", "d", "e", "f", "x","y","z","t"]:
        var_dict[v] = VarNode(v)

    datasetNames = ["dataset2_64bit"]
    for datasetName in datasetNames:
        with open(os.path.join(DATASET_PATH, datasetName+".txt"), newline='') as csvfile:
            spamreader = csv.reader(csvfile, delimiter=',')
            i = 0
            for row in spamreader:
                if row[0].startswith("#"): continue
                if i >= skip: yield (datasetName, str_to_ast(row[0], var_dict), str_to_ast(row[1], var_dict))
                i += 1
                if maximum != -1 and i >= maximum: break

def getDatasetCount():
    return 1