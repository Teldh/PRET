# -*- coding: utf-8 -*-
"""
Created on Fri Jul 12 16:12:05 2019

@author: marco mochi
"""
import math
from app import db
from app.models import Baseline_Methods, Bs_status, Bs_threshold
import sys


class Method_5():

    def __init__(self, words, text, bid, cap,threshold):
        self.words = words
        self.text_dict = text  # dictionary in which keys are the number of sub chapter and values are the corresponding text
        self.bid = bid
        self.cap = cap
        self.threshold = threshold
        self.tocValue = dict.fromkeys(words)
        self.tocDistance = {}
        for word in self.words:
            self.tocValue[word] = []

    def toc(self, a, b):
        """ Evaluate the toc value followinf the formula of the paper"""
        numa = a.split(".")
        numb = b.split(".")
        i = 0
        # Check if a and b has the same length. If not add a 0 to a or b
        while (len(numa) != len(numb)):
            if (len(numa) > len(numb)):
                numb.append("0")
            else:
                numa.append("0")

        while (numa[i] == numb[i]):
            i += 1

        return float((float(numa[i]) - float(numb[i])) / float(math.pow(2, int(i + 1) - 1)))

    def initializeTocValue(self):
        """ it find all cahpter in which each single word appears  and it populate the tocValue dictionary """
        for word in self.words:

            if '-' in word:
                list_word = str(word).split('-')
            elif '/' in word:
                list_word = str(word).split('/')
            else:
                list_word = str(word).split()

            for cap, text in self.text_dict.items():
                if all(word.lower() in text.lower() for word in list_word):
                    self.tocValue[word].append(cap)
                    # tocValue contiene quindi il termine e i capitoli dove appare

    def populate_db(self):
        for key, value in self.tocDistance.items():

            concept = key.split("_")[0]
            lemma = key.split("_")[1]
            bs = Baseline_Methods.query.filter_by(bid=self.bid, cap=self.cap, lemma1=concept, lemma2=lemma).first()
            if not value:
                value = 0
            if not bs:
                bs = Baseline_Methods(bid=self.bid, cap=self.cap, lemma1=concept, lemma2=lemma, m5=float(value))
                db.session.add(bs)
            else:
                bs.m5 = float(value)
        db.session.commit()

    def updateStatus(self, status):
        row = Bs_status.query.filter_by(bid=self.bid, cap=self.cap, method=5).first()
        if not row:
            stato = Bs_status(bid=self.bid, cap=self.cap, method=5, status=status)
            db.session.add(stato)
        else:
            row.status = status
        db.session.commit()

    def method_5(self):
        try:
            self.updateStatus("running")
            print("running")
            self.initializeTocValue()  # crea tocValue dove tocValue[termine] = capitoli in cui compare

            for i, wordA in enumerate(self.words):
                for wordB in [x for x in self.words if x != wordA]:
                    self.tocDistance[wordA + "_" + wordB] = []
                    if len(self.tocValue[wordA]) > 0 and len(self.tocValue[wordB]) > 0:
                        for capA in self.tocValue[wordA]:
                            for capB in self.tocValue[wordB]:

                                if capA != capB:
                                    self.tocDistance[wordA + "_" + wordB].append(self.toc(capA, capB))

                        if len(self.tocDistance[wordA + "_" + wordB]) > 0:
                            self.tocDistance[wordA + "_" + wordB] = sum(self.tocDistance[wordA + "_" + wordB]) / len(
                                self.tocDistance[wordA + "_" + wordB])
                            # tocDistance è distanza tra A e B, quindi distanza da lemma1 a lemma2

            db.session.add(Bs_threshold(bid=self.bid, cap=self.cap, method=5, threshold=self.threshold))
            self.populate_db()
            self.updateStatus("succeeded")
        except:
            self.updateStatus("failed")
            print("error:", sys.exc_info())
            raise
