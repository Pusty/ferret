import os
import csv
from ferret import VarNode, str_to_ast


# msimba.txt, mba_obf_linear.txt

msimba_txt = []
msimba_txt_groundtruth = []

mba_obf_linear_txt = []
mba_obf_linear_txt_groundtruth = []


def parseDataset(maximum=-1):
    if len(msimba_txt) != 0: return [("msimba_txt", msimba_txt, msimba_txt_groundtruth), ("mba_obf_linear_txt", mba_obf_linear_txt, mba_obf_linear_txt_groundtruth)]
    PROJECT_PATH = os.getcwd()
    DATASET_PATH = os.path.join(
        PROJECT_PATH,"thirdparty", "MSiMBA", "MSiMBA", "Datasets"
    )

    var_dict = {}
    for v in ["a","b","x","y","z","t"]:
        var_dict[v] = VarNode(v)

    with open(os.path.join(DATASET_PATH, "msimba.txt"), newline='') as csvfile:
        spamreader = csv.reader(csvfile, delimiter=',')
        i = 0
        for row in spamreader:
            if row[0].startswith("#"): continue
            msimba_txt.append(str_to_ast(row[0], var_dict))
            msimba_txt_groundtruth.append(str_to_ast(row[1], var_dict))
            i += 1
            if maximum != -1 and i >= maximum: break

    with open(os.path.join(DATASET_PATH, "mba_obf_linear.txt"), newline='') as csvfile:
        spamreader = csv.reader(csvfile, delimiter=',')
        i = 0
        for row in spamreader:
            if row[0].startswith("#"): continue
            mba_obf_linear_txt.append(str_to_ast(row[0], var_dict))
            mba_obf_linear_txt_groundtruth.append(str_to_ast(row[1], var_dict))
            i += 1
            if maximum != -1 and i >= maximum: break

    print("MSimBA Dataset parsed")
    return [("msimba_txt", msimba_txt, msimba_txt_groundtruth), ("mba_obf_linear_txt", mba_obf_linear_txt, mba_obf_linear_txt_groundtruth)]
    

def getDataset(maximum=-1, skip=0):
    PROJECT_PATH = os.getcwd()
    DATASET_PATH = os.path.join(
        PROJECT_PATH,"thirdparty", "MSiMBA", "MSiMBA", "Datasets"
    )

    var_dict = {}
    for v in ["a","b","x","y","z","t"]:
        var_dict[v] = VarNode(v)


    datasetNames = ["msimba", "mba_obf_linear"]
    for datasetName in datasetNames:
        with open(os.path.join(DATASET_PATH, datasetName+".txt"), newline='') as csvfile:
            spamreader = csv.reader(csvfile, delimiter=',')
            i = 0
            for row in spamreader:
                if row[0].startswith("#"): continue
                if i >= skip: yield (datasetName,  str_to_ast(row[0], var_dict), str_to_ast(row[1], var_dict))
                i += 1
                if maximum != -1 and i >= maximum: break

def getDatasetCount():
    return 2