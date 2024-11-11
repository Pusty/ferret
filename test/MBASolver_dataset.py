import os
import csv
from ferret import BitVec


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

    a = BitVec.var("a")
    b = BitVec.var("b")
    x = BitVec.var("x")
    y = BitVec.var("y")
    z = BitVec.var("z")
    t = BitVec.var("t")

    with open(os.path.join(DATASET_PATH, "pldi_dataset_linear_MBA.txt"), newline='') as csvfile:
        spamreader = csv.reader(csvfile, delimiter=',')
        i = 0
        for row in spamreader:
            if row[0].startswith("#"): continue
            pldi_dataset_linear_MBA.append(eval(row[0]))
            pldi_dataset_linear_MBA_groundtruth.append(eval(row[1]))
            i += 1
            if maximum != -1 and i >= maximum: break

    with open(os.path.join(DATASET_PATH, "pldi_dataset_nonpoly_MBA.txt"), newline='') as csvfile:
        spamreader = csv.reader(csvfile, delimiter=',')
        i = 0
        for row in spamreader:
            if row[0].startswith("#"): continue
            pldi_dataset_nonpoly_MBA.append(eval(row[0]))
            pldi_dataset_nonpoly_MBA_groundtruth.append(eval(row[1]))
            i += 1
            if maximum != -1 and i >= maximum: break

    with open(os.path.join(DATASET_PATH, "pldi_dataset_poly_MBA.txt"), newline='') as csvfile:
        spamreader = csv.reader(csvfile, delimiter=',')
        i = 0
        for row in spamreader:
            if row[0].startswith("#"): continue
            pldi_dataset_poly_MBA.append(eval(row[0]))
            pldi_dataset_poly_MBA_groundtruth.append(eval(row[1]))
            i += 1
            if maximum != -1 and i >= maximum: break

    print("MBA-Solver Dataset parsed")
    return [("pldi_dataset_linear_MBA", pldi_dataset_linear_MBA, pldi_dataset_linear_MBA_groundtruth), ("pldi_dataset_nonpoly_MBA", pldi_dataset_nonpoly_MBA, pldi_dataset_nonpoly_MBA_groundtruth), ("pldi_dataset_poly_MBA", pldi_dataset_poly_MBA, pldi_dataset_poly_MBA_groundtruth)]


def getDataset(maximum=-1, skip=0):
    PROJECT_PATH = os.getcwd()
    DATASET_PATH = os.path.join(
        PROJECT_PATH,"thirdparty", "MBA-Solver", "full-dataset"
    )

    a = BitVec.var("a")
    b = BitVec.var("b")
    x = BitVec.var("x")
    y = BitVec.var("y")
    z = BitVec.var("z")
    t = BitVec.var("t")

    datasetNames = ["pldi_dataset_linear_MBA", "pldi_dataset_nonpoly_MBA", "pldi_dataset_poly_MBA"]
    for datasetName in datasetNames:
        with open(os.path.join(DATASET_PATH, datasetName+".txt"), newline='') as csvfile:
            spamreader = csv.reader(csvfile, delimiter=',')
            i = 0
            for row in spamreader:
                if row[0].startswith("#"): continue
                if i >= skip: yield (datasetName, eval(row[0]), eval(row[1]))
                i += 1
                if maximum != -1 and i >= maximum: break