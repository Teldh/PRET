import codecs
import os
import glob

""" Computes the Fleiss' Kappa value as described in (Fleiss, 1971) """
"""https://en.wikibooks.org/wiki/Algorithm_Implementation/Statistics/Fleiss%27_kappa"""

DEBUG = False


def computeKappa(mat):
    """ Computes the Kappa value
        @param n Number of rating per subjects (number of human raters)
        @param mat Matrix[subjects][categories]
        @return The Kappa value """
    n = checkEachLineCount(mat)  # PRE : every line count must be equal to n
    N = len(mat)
    k = len(mat[0])

    if DEBUG:
        print
        n, "raters."
        print
        N, "subjects."
        print
        k, "categories."

    # Computing p[] (accordo sugli 0 e accordo sugli 1)
    p = [0.0] * k
    for j in range(k):
        p[j] = 0.0
        for i in range(N):
            p[j] += mat[i][j]
        p[j] /= N * n
    if DEBUG: print
    "p =", p

    # Computing P[]  (accordo su ogni singola coppia di concetti)
    P = [0.0] * N
    for i in range(N):
        P[i] = 0.0
        for j in range(k):
            P[i] += mat[i][j] * mat[i][j]
        P[i] = (P[i] - n) / (n * (n - 1))
    if DEBUG: print
    "P =", P

    # Computing Pbar (accordo osservato)
    Pbar = sum(P) / N
    if DEBUG: print
    "Pbar =", Pbar

    # Computing PbarE (accordo dovuto al caso)
    PbarE = 0.0
    for pj in p:
        PbarE += pj * pj
    if DEBUG: print
    "PbarE =", PbarE

    kappa = (Pbar - PbarE) / (1 - PbarE)
    if DEBUG: print
    "kappa =", kappa

    return kappa


def checkEachLineCount(mat):
    """ Assert that each line has a constant number of ratings
        @param mat The matrix checked
        @return The number of ratings
        @throws AssertionError If lines contain different number of ratings """
    n = sum(mat[0])

    assert all(sum(line) == n for line in mat[1:]), "Line count != %d (n value)." % n
    return n


def initialTerms():
    concepts_all = []
    # concetti estratti automaticamente condivisi da tutti gli annotatori (file txt esterno) [terminologia iniziale]
    InputTerminology = codecs.open("./concetti_tutti.txt.txt", "r", "utf-8").read()
    terminology = InputTerminology.split("\n")
    for concept in terminology:
        if concept:
            concepts_all.append(concept.upper())
    return concepts_all


def combineTerms(concepts_all):
    all_combs = []
    # creo tutte le possibili coppie di concetti automatici
    for term in concepts_all:
        for i in range(len(concepts_all)):
            if term != concepts_all[i]:
                combination = term + "-" + concepts_all[i]
                all_combs.append(combination)
    return all_combs

def computeFleiss(term_pairs, all_combs):
    matrix_fleiss = []

    for item in all_combs:
        countZero = 0
        countOne = 0
        for rater, values in term_pairs.items():
            lista = []
            if item not in values:
                countZero = countZero + 1
            if item in values:
                countOne = countOne + 1
        lista.insert(0, countZero)
        lista.insert(1, countOne)
        matrix_fleiss.append(lista)

    return computeKappa(matrix_fleiss)


'''
if __name__ == "__main__":
    prereqs = {}
    matrix_fleiss = []
    raters = []
    term_pairs = {}
    concepts_all = initialTerms()
    all_combs = combineTerms(concepts_all)
    extension = 'tab'
    for file in glob.glob('*.{}'.format(extension)):
        name = os.path.splitext(os.path.basename(file))[0]
        # print "file", name
        raters.append(name)
        term_pairs[name] = []
        with open(file) as data_file:
            reader = data_file.read().split("\n")
            for line in reader:
                if line:
                    # line="id	PREQ	TARGET	sent_id	weigth	agreem"
                    # line="num	NETWORK	PERSONAL_AREA_NETWORK	9	strong	5"
                    # considera solo le coppie che contengono termini della terminologia automatica
                    lineS = line.split("\t")
                    # if lineS[1] in concepts_all and lineS[2] in concepts_all: #scenario2
                    concept_pair = lineS[1] + "-" + lineS[2]
                    term_pairs[name].append(concept_pair)

    for item in all_combs:
        countZero = 0
        countOne = 0
        for rater, values in term_pairs.items():
            lista = []
            if item not in values:
                countZero = countZero + 1
            if item in values:
                countOne = countOne + 1
        lista.insert(0, countZero)
        lista.insert(1, countOne)
        matrix_fleiss.append(lista)

    kappa = computeKappa(matrix_fleiss)
'''