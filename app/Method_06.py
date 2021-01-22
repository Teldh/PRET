import pandas as pd
from app.burst_extractor import BurstExtractor
from app.weight_assigner import WeightAssigner
from app.weight_normalizer import WeightsNormalizer
import app.burst_results_processor as burst_proc
import nltk
from app.models import Baseline_Methods, Bs_status, Burst_params, Burst_params_allen, Allen_type, Burst_results, Burst_rel_allen
from app import db
import sys
from conllu import parse

class Method_6():

    def __init__(self, text, words, conll, bid, cap, s=1.05, gamma=0.0001, level=1, allen_weights=None,
                 use_inverses=False, max_gap=4, norm_formula="modified"):
        self.text = text
        self.words = words
        self.conll = parse(conll)
        self.bid = bid
        self.cap = cap

        #Kleinberg's parameters
        self.S = s
        self.GAMMA = gamma
        self.LEVEL = level

        #OCC_INDEX_FILE
        #Dataframe contentente le colonne "Lemma", "idFrase", "idParolaStart"
        #Quindi il lemma, in che frase appare e l'indice nella frase
        occurrences_index = []

        for index, sent in enumerate(self.conll):
            for index_word, word in enumerate(sent):
                if word["lemma"].upper() in [x.upper() for x in self.words]:
                    d = [word["lemma"].lower(), index, index_word]
                    occurrences_index.append(d)

        self.occurrences = pd.DataFrame(data=occurrences_index, columns=["Lemma", "idFrase", "idParolaStart"])


        # weights for Allen and type of normalization formula
        if allen_weights is None:
            self.ALLEN_WEIGHTS = {'equals': 2, 'before': 5, 'after': 0, 'meets': 3, 'met-by': 0,
                             'overlaps': 7, 'overlapped-by': 1, 'during': 7, 'includes': 7,
                             'starts': 4, 'started-by': 2, 'finishes': 2, 'finished-by': 8}
        else:
            self.ALLEN_WEIGHTS = allen_weights


        self.USE_INVERSES = use_inverses
        self.MAX_GAP = max_gap
        self.NORM_FORMULA = norm_formula

        # decide if preserve relations when giving direction to the burst matrix
        self.PRESERVE_RELATIONS = True



    def updateStatus(self, status):
        row = Bs_status.query.filter_by(bid=self.bid, cap=self.cap, method=6).first()
        if not row:
            stato = Bs_status(bid=self.bid, cap=self.cap, method=6, status=status)
            db.session.add(stato)
        else:
            row.status = status
        db.session.commit()

    def method_6(self):

        try:
            # FIRST PHASE: extract bursts
            #print("Extracting bursts...\n")

            burst_extr = BurstExtractor(text=self.text, wordlist=self.words)
            burst_extr.find_offsets(occ_index_file=None)
            burst_extr.generate_bursts(s=self.S, gamma=self.GAMMA)
            burst_extr.filter_bursts(level=self.LEVEL, save_monolevel_keywords=True, replace_original_results=True)
            burst_extr.break_bursts(burst_length=30, num_occurrences=3, replace_original_results=True)
            burst_res = burst_extr.bursts

            if burst_res.empty:
                raise ValueError("The chosen parameters do not produce results")

            # obtain json with first, last, ongoing, unique tags
            bursts_json = burst_proc.get_json_with_bursts(burst_res, self.occurrences)



            # SECOND PHASE: detect relations between bursts and assign weights to them
            #print("Detecting Allen's relations and assign weights to burst pairs...\n")
            weight_assigner = WeightAssigner(bursts=burst_res,
                                             relations_weights=self.ALLEN_WEIGHTS)
            weight_assigner.detect_relations(max_gap=self.MAX_GAP, alpha=0.05, find_also_inverse=self.USE_INVERSES)
            # output data for the gantt interface and ML projects
            burst_pairs_df = weight_assigner.burst_pairs

            bursts_weights = weight_assigner.bursts_weights


            # THIRD PHASE: normalize the bursts' weights
            #print("Normalizing the matrix with weights of burst pairs...\n")
            weight_norm = WeightsNormalizer(bursts=burst_res,
                                            burst_pairs=burst_pairs_df,
                                            burst_weight_matrix=bursts_weights)
            weight_norm.normalize(formula=self.NORM_FORMULA, occ_index_file=self.occurrences)

            burst_norm = weight_norm.burst_norm.round(decimals=3)


            # FINAL STEP: give directionality to bursts
            #print("Giving directionality to the concept matrix built with bursts...\n")

            directed_burst = burst_proc.give_direction_using_first_burst(undirected_matrix=burst_norm,
                                                                         bursts_results=burst_res,
                                                                         indexes=self.occurrences,
                                                                         level=self.LEVEL, preserve_relations=self.PRESERVE_RELATIONS)

            # add rows and columns in the matrices for possible discarded terms
            #print("\nAdding rows and columns for missing concepts in the burst matrix...\n")
            missing_terms = [term for term in self.words
                             if term not in directed_burst.index]

            for term in missing_terms:
                directed_burst.loc[term] = 0
                directed_burst[term] = 0

            #print("Shape of final directed burst matrix:", directed_burst.shape)

            # get an edgelist with the extracted prerequisite relations
            #print("Getting an edgelist with the extracted prerequisite relations...\n")
            sorted_edgelist = pd.DataFrame(burst_proc.to_edgelist(directed_burst),
                                           columns=["prerequisite", "target", "weight"])



            ### SALVATAGGIO DATI IN DATABASE

            # salvo risultati
            for row in sorted_edgelist.itertuples():
                bs = Baseline_Methods.query.filter_by(bid=self.bid, cap=self.cap, lemma1=row.target, lemma2=row.prerequisite).first()
                if not bs:
                    bs = Baseline_Methods(bid=self.bid, cap=self.cap, lemma1=row.target, lemma2=row.prerequisite, m6=row.weight)
                    db.session.add(bs)
                else:
                    bs.m6 = row.weight

            # salvo i parametri usati
            params = Burst_params.query.filter_by(bid=self.bid, cap=self.cap).first()
            if not params:
                params = Burst_params(bid=self.bid, cap=self.cap, s=self.S, gamma=self.GAMMA, level=self.LEVEL)
                db.session.add(params)
            else:
                params.s = self.S
                params.gamma = self.GAMMA
                params.level = self.LEVEL


            for typ in self.ALLEN_WEIGHTS:
                allen = Burst_params_allen.query.filter_by(bid=self.bid, cap=self.cap, type=typ).first()
                if not allen:
                    allen = Burst_params_allen(bid=self.bid, cap=self.cap, type=typ, weight=self.ALLEN_WEIGHTS[typ])
                    db.session.add(allen)
                else:
                    allen.weight=self.ALLEN_WEIGHTS[typ]


            # salvo burst results
            old_bursts = Burst_results.query.filter_by(bid=self.bid, cap=self.cap).all()

            for old in old_bursts:
                db.session.delete(old)

            for burst in bursts_json:
                b = Burst_results.query.filter_by(burst_id=burst["ID"], bid=self.bid, cap=self.cap).first()

                if not b:
                    b = Burst_results(burst_id=burst["ID"], bid=self.bid, cap=self.cap, lemma=burst["concept"],
                                      start=burst["startSent"], end=burst["endSent"], freq=burst["freqOfTerm"],
                                      status=burst["status"])
                    db.session.add(b)
                else:
                    b.lemma = burst["concept"]
                    b.start = burst["startSent"]
                    b.end = burst["endSent"]
                    b.freq = burst["freqOfTerm"]
                    b.status = burst["status"]


            # salvo relazioni tra le coppie di burst
            old_bursts_pairs = Burst_rel_allen.query.filter_by(bid=self.bid, cap=self.cap).all()

            for old in old_bursts_pairs:
                db.session.delete(old)

            for burst_pair in burst_pairs_df.itertuples():
                b = Burst_rel_allen.query.filter_by(bid=self.bid, cap=self.cap, burst1=burst_pair.Bx_id, burst2=burst_pair.By_id).first()

                if not b:
                    b = Burst_rel_allen(bid=self.bid, cap=self.cap,
                                        burst1=burst_pair.Bx_id, burst2=burst_pair.By_id, type=burst_pair.Rel)

                    db.session.add(b)
                else:
                    b.type = burst_pair.Rel


            db.session.commit()
            self.updateStatus("modifiable")
        except ValueError as e:
            print("error:", sys.exc_info())
            self.updateStatus("failed")
            raise e