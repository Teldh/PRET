# -*- coding: utf-8 -*-
"""
Created on Sun Jun 16 22:10:13 2019

@author: io
"""
import nltk;
from nltk.corpus import wordnet as wn;
from nltk.corpus import PlaintextCorpusReader
from app import db
from app.models import Baseline_Methods, Conll, Bs_status
from app.utils import id_phrase
from conllu import parse
import sys



class Method_2():
    """ Class for evaluating prerequisite relationship using lexical pattern"""
    
    lex_pattern = ["/y/ such as /x/ ", "/y/ such as a /x/ ", "such /y/ as an /x/", "/x/ is a /y/", "/x/ is an /y/", "/y/ includes /x/", "/y/ includs /x/", "/y/ including /x/", "/x/ is called /y/", "/x/ are called /y/", "/x/, one of /y/", "/x/ and other /y/", "/x/ or other /y/", "/y/ consist of /x/", "/y/ consists of /x/", "/y/ like /x/", "/y/, specially /x/", "/x/ in /y/", "/x/ belong to /y/"]
    
    def __init__(self, words, conll, text, bid, cap):
        self.sentence = parse(conll)
        self.words = words
        self.text = text
        self.bid = bid
        self.cap = cap
        self.pre_req = dict.fromkeys(words)
        self.phrase_id = {}
        self.phrase = {}
        for word in self.pre_req:
            self.pre_req[word] = []



    
    def pattern(self, word, prereq):
        for phrase in self.lex_pattern:
            phrase = phrase.replace("/x/", word)
            phrase = phrase.replace("/y/", prereq)

            result = self.text.find(phrase)
                
            if result != -1:
                sentence_id = self.id_to_sentence(result)

                # Se in questa frase non ci sono ancora relazioni
                if sentence_id not in list(self.phrase_id.values()):
                    if prereq not in self.pre_req[word]:
                        self.pre_req[word].append(prereq)
                    self.phrase_id[word + "_" + prereq] = sentence_id
                    self.phrase[word + "_" + prereq] = phrase

                else:
                    '''nel caso di più relazioni trovate nella stessa frase devo prenderle tutte
                    ma nel caso di una relazione multiword devo prendere solo quella con più parole'''

                    new_rel = phrase
                    old_rels = []

                    # prendo tutte le relazioni già messe nella frase
                    for r in self.phrase_id:
                        if self.phrase_id[r] == sentence_id:
                            old_rels.append(r)

                        #  per ogni relazione nella frase
                    for old_rel in old_rels:
                        lemmas = old_rel.split("_")

                        # se una nuova relazione contiene una relazione vecchia (nella stessa frase),
                        # elimino la vecchia e metto la nuova
                        # ad esempio:  "phone network is an internet" contiene "network is an internet" -> la levo
                        if self.phrase[old_rel] in new_rel:

                            self.pre_req[lemmas[0]].remove(lemmas[1])
                            del self.phrase_id[old_rel]
                            del self.phrase[old_rel]
                            if prereq not in self.pre_req[word]:
                                self.pre_req[word].append(prereq)
                            self.phrase_id[word + "_" + prereq] = sentence_id
                            self.phrase[word + "_" + prereq] = new_rel

                        # se la nuova relazione non è contenuta in una vecchia, aggiungo la relazione
                        elif new_rel not in self.phrase[old_rel]:
                            if prereq not in self.pre_req[word]:
                                self.pre_req[word].append(prereq)
                            self.phrase_id[word + "_" + prereq] = sentence_id
                            self.phrase[word + "_" + prereq] = new_rel

               
    def id_to_sentence(self, key):
        stop = 0
        for ids, phrase in enumerate(self.sentence):
            for words in phrase:
                stop += len(words["form"])
                stop += 1 # aggiungo lunghzza dello spazio tra una parola e l'altra
            if stop >= key:
                return ids + 1
                 
            
        
    
    def populate_db(self, words, bid, cap):
        for concept in words:
            for lemma in [lemma for lemma in words if concept != lemma]:
                bs = Baseline_Methods.query.filter_by(bid=bid, cap=cap, lemma1=concept, lemma2=lemma).first()
                if not bs:
                    if lemma in self.pre_req[concept]:
                        try:
                            phrase = int(self.phrase_id[concept + "_" + lemma])
                        except:
                            phrase = 0
                        bs = Baseline_Methods(bid=bid, cap=cap, lemma1=concept, lemma2=lemma, m2=1, m2_sentence = phrase)
                        db.session.add(bs)
                    else:
                        bs = Baseline_Methods(bid=bid, cap=cap, lemma1=concept, lemma2=lemma, m2=0, m2_sentence = 0)
                        db.session.add(bs)
                else: 
                   if lemma in self.pre_req[concept]:
                       try:
                           phrase = int(self.phrase_id[concept + "_" + lemma])
                       except:
                           phrase = 0
                       bs.m2 = 1    
                       bs.m2_sentence = phrase
                   else:
                       bs.m2 = 0
                       bs.m2_sentence = 0
                       
        db.session.commit()

    def updateStatus(self, status):
        row = Bs_status.query.filter_by(bid=self.bid, cap=self.cap, method=2).first()
        if not row:
            stato = Bs_status(bid=self.bid, cap=self.cap, method=2, status=status)
            db.session.add(stato)
        else:
            row.status = status
        db.session.commit()


    def method_2(self):
        try:
            self.updateStatus("running")
            for word in self.words:
                for prereq in [x for x in self.words if x != word]:
                    self.pattern(word, prereq)

            self.populate_db(self.words, self.bid, self.cap)
            self.updateStatus("succeeded")
        except:
            self.updateStatus("failed")
            print("error:", sys.exc_info())
            raise
            
                
    
                
