import os
import csv
from ferret import BitVec


# dataset2_64bit.txt

dataset2_64bit = []
dataset2_64bit_groundtruth = []


def parseDataset(maximum=-1):
    if len(dataset2_64bit) != 0: return [("dataset2_64bit", dataset2_64bit, dataset2_64bit_groundtruth)]
    PROJECT_PATH = os.getcwd()
    DATASET_PATH = os.path.join(
        PROJECT_PATH,"thirdparty", "MBA-Blast", "dataset"
    )

    a = BitVec.var("a")
    b = BitVec.var("b")
    c = BitVec.var("c")
    d = BitVec.var("d")
    e = BitVec.var("e")
    f = BitVec.var("f")
    x = BitVec.var("x")
    y = BitVec.var("y")
    z = BitVec.var("z")
    t = BitVec.var("t")

    with open(os.path.join(DATASET_PATH, "dataset2_64bit.txt"), newline='') as csvfile:
        spamreader = csv.reader(csvfile, delimiter=',')
        i = 0
        for row in spamreader:
            if row[0].startswith("#"): continue
            dataset2_64bit.append(eval(row[0]))
            dataset2_64bit_groundtruth.append(eval(row[1]))
            i += 1
            if maximum != -1 and i >= maximum: break

    print("MBA-Blast Dataset parsed")
    return [("dataset2_64bit", dataset2_64bit, dataset2_64bit_groundtruth)]


def getDataset(maximum=-1, skip=0):
    PROJECT_PATH = os.getcwd()
    DATASET_PATH = os.path.join(
        PROJECT_PATH,"thirdparty", "MBA-Blast", "dataset"
    )

    a = BitVec.var("a")
    b = BitVec.var("b")
    c = BitVec.var("c")
    d = BitVec.var("d")
    e = BitVec.var("e")
    f = BitVec.var("f")
    x = BitVec.var("x")
    y = BitVec.var("y")
    z = BitVec.var("z")
    t = BitVec.var("t")
    datasetNames = ["dataset2_64bit"]
    for datasetName in datasetNames:
        with open(os.path.join(DATASET_PATH, datasetName+".txt"), newline='') as csvfile:
            spamreader = csv.reader(csvfile, delimiter=',')
            i = 0
            for row in spamreader:
                if row[0].startswith("#"): continue
                if i >= skip: yield (datasetName, eval(row[0]), eval(row[1]))
                i += 1
                if maximum != -1 and i >= maximum: break