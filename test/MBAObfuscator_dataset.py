import os
import csv
from ferret import BitVec


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

    x = BitVec.var("x")
    y = BitVec.var("y")
    z = BitVec.var("z")
    t = BitVec.var("t")

    with open(os.path.join(DATASET_PATH, "ground.linear.nonpoly.txt"), newline='') as csvfile:
        spamreader = csv.reader(csvfile, delimiter=',')
        i = 0
        for row in spamreader:
            if row[0].startswith("#"): continue
            ground_linear_nonpoly.append(eval(row[2]))
            ground_linear_nonpoly_groundtruth.append(eval(row[1]))
            i += 1
            if maximum != -1 and i >= maximum: break

    with open(os.path.join(DATASET_PATH, "ground.linear.poly.txt"), newline='') as csvfile:
        spamreader = csv.reader(csvfile, delimiter=',')
        i = 0
        for row in spamreader:
            if row[0].startswith("#"): continue
            ground_linear_poly.append(eval(row[2]))
            ground_linear_poly_groundtruth.append(eval(row[1]))
            i += 1
            if maximum != -1 and i >= maximum: break

    print("MBA-Obfuscator Dataset parsed")
    return [("ground_linear_nonpoly", ground_linear_nonpoly, ground_linear_nonpoly_groundtruth), ("ground_linear_poly", ground_linear_poly, ground_linear_poly_groundtruth)]

def getDataset(maximum=-1, skip=0):
    PROJECT_PATH = os.getcwd()
    DATASET_PATH = os.path.join(
        PROJECT_PATH,"thirdparty", "MBA-Obfuscator", "samples"
    )

    x = BitVec.var("x")
    y = BitVec.var("y")
    z = BitVec.var("z")
    t = BitVec.var("t")

    datasetNames = ["ground_linear_nonpoly", "ground_linear_poly"]
    for datasetName in datasetNames:
        with open(os.path.join(DATASET_PATH, datasetName+".txt"), newline='') as csvfile:
            spamreader = csv.reader(csvfile, delimiter=',')
            i = 0
            for row in spamreader:
                if row[0].startswith("#"): continue
                if i >= skip: yield (datasetName, eval(row[2]), eval(row[1]))
                i += 1
                if maximum != -1 and i >= maximum: break