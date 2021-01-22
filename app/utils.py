# -*- coding: utf-8 -*-
import requests, re, ast
import app
from app import db
import json
from nltk import WordNetLemmatizer
from conllu import parse
import pandas as pd
from collections import Counter
from app.graph_analyzer import create_graphs, compute_metrics, detect_loops, detect_transitive_edges, detect_clusters, create_graph_dict, get_roots, longest_path
from app.models import Baseline_Methods, Annotations, Annotation_user, Annotation_types, Terminology, goldStandard, Terminology_reference, Revision_status, Revised_annotations,Bs_threshold,User, Bs_status
import sys

def conll_gen(file):
    """" Takes a text as input (file) and return a conll file (sentence)"""
    
    files = {
           'data': file,
           'model' : (None, 'english-ewt-ud-2.4-190531'),
           'tokenizer': (None, ''),
           'tagger': (None, ''),
           'parser': (None, ''),
       }

    r = requests.post('http://lindat.mff.cuni.cz/services/udpipe/api/process', files=files)
    re = r.json()
    sentence = re['result']
    return sentence

def id_phrase(conll, result):
    """ Take a file conll and a list of phrases as input and return the phrase id of that phrases """
    sentence = parse(conll)
    phraseid = []
    
    for x in [frasi for frasi in result]:
        list_word = str(x).split()
        i = 0
        check = []
        for ids, phrase in enumerate(sentence):
            for words in phrase:
                if (words["form"] == list_word[i]):
                    check.append(words["form"])
                    i += 1
                    if all(word in check for word in list_word):
                        phraseid.append(ids)
                        i = 0
                        break
                else:
                    check.clear()
                    i = 0
                
    
    return(phraseid)

def conll_to_text0(conll, start):
    """ From conll format to string with an index for starting """
    sentence = parse(conll)    
    check = ""
    for phrase in sentence[start:]:
        for words in phrase:
            check += words["form"] + " "
    return(check)
        
def conll_to_text1(conll, start, end):
    """ From conll format to string with an index for starting and ending """
    sentence = parse(conll)
    check = ""
    for phrase in sentence[start:end]:
        for words in phrase:
            check += words["form"] + " "
    return(check)
    
def parse_sentId(conll):
    """ Get the id of all the phrases """
    sentence = parse(conll)
    sentList = []
    data = {}
    text = ""
    for ids, phrase in enumerate(sentence):
        for words in phrase:
            text += words["form"] + " "    
        data['sent_id'] = ids + 1    
        data['text'] = text
        data['type'] = 'normal sentence'
        json_data = json.dumps(data)
        sentList.append(json_data)
    return(sentList)
    
def parse_tokToConcept(conll, words):
    lemmatizer = WordNetLemmatizer()
    text = conll_to_text0(conll, 0)
    tokToConcept = {}
    flag = True
    for word in words:
        position = []
        list_word = str(word).split()
        

        for index, word in enumerate(text.split()):
            if(flag):
                check = [(word.lower())]
            else:
                check.append((word.lower()))
            if all(word.lower() in check for word in list_word):
                position.append(index)
                flag = True
                continue
            if all(word in list_word for word in check):
                flag = False
            else:
                flag = True
        phrase = ""
        for word in list_word:
            phrase += word + " "
        tokToConcept.update({phrase: position})
    for key in sorted(tokToConcept):
        print(key, tokToConcept[key])
            
def data_analysis(conll, words, sentences, bid, cap, method):
    """ Create the two csv to use graph analyzer """
    lemmatizer = WordNetLemmatizer()
    df = pd.DataFrame(columns=['ID', 'name', 'frequence', 'sections', 'sentence', 'subsidiaries'])  
    dfAnnotation = pd.DataFrame(columns=['prerequisites', 'subsidiaries'])
    metrics = {}
    tokens = 0
    text = ""
    sentPhrase = ""
    sent = []
    appear = []
    section = []
    subsidiaries = []
    sentence = parse(conll)
    metrics['default concepts'] = len(words)

    # Add manual added concept if manual annotation
    if method not in ["1", "2", "3","4","5","6"]:
        new_words = set([])
        rel = Annotations.query.filter_by(bid=bid, cap=cap).all()
        uid = method.split(".")[1]
        for item in rel:
            if (type(item.lemma1) is str):
                get = Annotation_user.query.filter_by(aid=item.aid).first()
                user = User.query.filter_by(uid=get.uid).first()
                new_words.add(item.lemma1.lower())
            elif(type(item.lemma2) is str):
                get = Annotation_user.query.filter_by(aid=item.aid).first()
                user = User.query.filter_by(uid=get.uid).first()
                new_words.add(item.lemma2.lower())

            try:
                int(item.lemma1)
            except ValueError:
                if (Annotation_user.query.filter_by(aid=item.aid).first() and str(Annotation_user.query.filter_by(aid=item.aid).first().uid) == str(uid)):
                    new_words.add(item.lemma1.lower())
            try:
                int(item.lemma2)
            except ValueError:
                if (Annotation_user.query.filter_by(aid=item.aid).first() and str(Annotation_user.query.filter_by(aid=item.aid).first().uid) == str(uid)):
                    new_words.add(item.lemma2.lower())
        metrics['entered concepts'] = len(new_words)
        words.extend(new_words)
    
    
    # Prepare sentence and text
    for ids, phrase in enumerate(sentence):
        for word in phrase:
            tokens += 1
            text += lemmatizer.lemmatize(word["form"]) + " "
            sentPhrase += lemmatizer.lemmatize(word["form"]) + " "
        sent.append(sentPhrase)
        sentPhrase = ""
      
    metrics['tokens'] = tokens
    metrics['sentences'] = len(sentence)
    metrics['strong relations'] = 0
    metrics['weak relations'] = 0
    metrics['unique relations'] = []

    revisione_fatta = False
    if method not in ['1','2','3','4','5','6']:
        if Revision_status.query.filter_by(bid=bid, cap=cap, uid=method.split(".")[1]).first().status == "Finished":
            revisione_fatta = True
     
    for i, word in enumerate(words):
        freq = text.count(word)
        # Check if a word is in a sent
        for k, phrase in enumerate(sent):
            if word in phrase:
                appear.append(k)
        # Check if a word is in a section
        for j, number in enumerate(sentences):
            if (j + 1) < len(sentences):
                if any(phraseId > number.sentence and phraseId < sentences[j+1].sentence for phraseId in appear):
                    section.append(int(number.section.split(".")[-1]))
            else:
                if any(phraseId > number.sentence for phraseId in appear):
                    section.append(int(number.section.split(".")[-1]))

        # Get all the relationship for baseline methods            
        if method in ["1", "2", "3","4","5","6"]:
            subsidiaries = Baseline_Methods.query.filter_by(lemma2=word, bid=bid, cap=cap).all()
            if method == "1":
                subsidiaries = [candidate.lemma1 for candidate in subsidiaries if candidate.m1 == 1]
                for subs in subsidiaries:
                    row = pd.Series({"prerequisites": word, "subsidiaries": subs})
                    dfAnnotation = dfAnnotation.append(row, ignore_index=True)
                    if (word, subs) not in metrics["unique relations"]:
                        metrics["unique relations"].append((word, subs))
            elif method == "2":
                subsidiaries = [candidate.lemma1 for candidate in subsidiaries if candidate.m2 == 1]
                for subs in subsidiaries:
                    row = pd.Series({"prerequisites": word, "subsidiaries": subs})
                    dfAnnotation = dfAnnotation.append(row, ignore_index=True)
                    if (word, subs) not in metrics["unique relations"]:
                        metrics["unique relations"].append((word, subs))
            elif method == "3":
                threshold = Bs_threshold.query.filter_by(bid=bid, cap=cap, method=3).first().threshold

                target_terms = []
                #subsidiaries = [candidate.lemma1 for candidate in subsidiaries if candidate.m3 and (candidate.m3 > threshold)]
                for c in subsidiaries:
                    if c.m3 is not None:
                        if c.m3 > threshold:
                            target_terms.append(c.lemma1)

                for subs in target_terms:
                    threshold = Baseline_Methods.query.filter_by(lemma2=word, lemma1=subs, bid=bid, cap=cap).all()
                    for num in threshold:
                        row = pd.Series({"prerequisites": word, "subsidiaries": subs, "threshold": num.m3})
                        dfAnnotation = dfAnnotation.append(row, ignore_index=True)
                        if (word, subs) not in metrics["unique relations"]:
                            metrics["unique relations"].append((word, subs))


            elif method == "4":
                subsidiaries = [candidate.lemma1 for candidate in subsidiaries if candidate.m4 == 1]
                for subs in subsidiaries:
                    row = pd.Series({"prerequisites": word, "subsidiaries": subs})
                    dfAnnotation = dfAnnotation.append(row, ignore_index=True)
                    if (word, subs) not in metrics["unique relations"]:
                        metrics["unique relations"].append((word, subs))

            elif method == "5":
                threshold = Bs_threshold.query.filter_by(bid=bid, cap=cap, method=5).first().threshold
                target_terms = []
                # subsidiaries = [candidate.lemma1 for candidate in subsidiaries if candidate.m3 and (candidate.m5 > threshold)]

                for c in subsidiaries:
                    if c.m5 is not None:
                        if c.m5 > threshold:
                            target_terms.append(c.lemma1)

                for subs in target_terms:
                    threshold = Baseline_Methods.query.filter_by(lemma2=word,lemma1 = subs, bid=bid, cap=cap).all()
                    for num in threshold:

                        row = pd.Series({"prerequisites": word, "subsidiaries": subs,"threshold": num.m5})
                        dfAnnotation = dfAnnotation.append(row, ignore_index=True)
                        if (word, subs) not in metrics["unique relations"]:
                            metrics["unique relations"].append((word, subs))

            elif method == "6":
                threshold = Bs_threshold.query.filter_by(bid=bid, cap=cap, method=6).first().threshold
                target_terms = []
                # subsidiaries = [candidate.lemma1 for candidate in subsidiaries if candidate.m6 and (candidate.m3 > threshold)]

                for c in subsidiaries:
                    if c.m6 is not None:
                        if c.m6 > threshold:
                            target_terms.append(c.lemma1)

                for subs in target_terms:
                    threshold = Baseline_Methods.query.filter_by(lemma2=word, lemma1=subs, bid=bid, cap=cap).all()
                    for num in threshold:
                        row = pd.Series({"prerequisites": word, "subsidiaries": subs, "threshold": num.m6})
                        dfAnnotation = dfAnnotation.append(row, ignore_index=True)
                        if (word, subs) not in metrics["unique relations"]:
                            metrics["unique relations"].append((word, subs))
        # Get relationships for users annotation
        else:
            uid = method.split(".")[1]
            
            subsidiaries_aid = Annotations.query.filter_by(lemma2=find_term(word), bid=bid, cap=cap).all()
            for candidate in subsidiaries_aid:

                # la stessa relazione potrebbe essere stata messa piu volte dallo stesso utente
                anns = Annotation_user.query.filter_by(aid=candidate.aid, uid=uid).all()

                for annUsr in anns:
                    #se revisione è stata fatta e questa relazione è stata revisionata
                    if revisione_fatta and Revised_annotations.query.filter_by(ann_user_id=annUsr.ann_user_id).first() is not None:
                        # se rev_id = 1 allora la relazione è stata eliminata
                        if Revised_annotations.query.filter_by(ann_user_id=annUsr.ann_user_id).first().rev_id == 1:
                            annUsr = None

                    if annUsr is not None:
                        peso_cambiato = False
                        #se rev_id = 2 allora il peso è stato cambiato
                        if revisione_fatta and Revised_annotations.query.filter_by(ann_user_id=annUsr.ann_user_id).first() is not None :
                            peso_cambiato = Revised_annotations.query.filter_by(ann_user_id=annUsr.ann_user_id).first().rev_id == 2

                        if not peso_cambiato:
                            if annUsr.ann_type == 'weak':
                                metrics['weak relations'] += 1
                            elif annUsr.ann_type == 'strong':
                                metrics['strong relations'] += 1
                        else:
                            if annUsr.ann_type == 'strong':
                                metrics['weak relations'] += 1
                            elif annUsr.ann_type == 'weak':
                                metrics['strong relations'] += 1

                        if (candidate.lemma1, candidate.lemma2) not in metrics["unique relations"]:
                            metrics["unique relations"].append((candidate.lemma1, candidate.lemma2))

                        term = Terminology.query.filter_by(tid=candidate.lemma1).first()
                        if(term):
                            term = term.lemma.lower()
                            subsidiaries.append(term)
                        else:
                            term = candidate.lemma1.lower()
                            subsidiaries.append(candidate.lemma1.lower())


                        #print(word.lower(),term,annUsr.ann_type)

                        row = pd.Series({"prerequisites": word.lower(), "subsidiaries": term, "weight":annUsr.ann_type })
                        dfAnnotation = dfAnnotation.append(row, ignore_index=True)

        row = pd.Series({"ID": i, "name": word, "frequence": freq, "sections": section, "sentence": appear,
                         "subsidiaries": [sub for sub in subsidiaries]})
        df = df.append(row, ignore_index=True)
            
        appear = []
        section = []
        subsidiaries = []
    
    return (dfAnnotation, df, metrics, words)


def data_analysis_simple_graph(conll, words, sentences, bid, cap, method):
    """ Create the two csv to use graph analyzer """
    lemmatizer = WordNetLemmatizer()
    df = pd.DataFrame(columns=['ID', 'name', 'frequence', 'sections', 'sentence', 'subsidiaries'])
    dfAnnotation = pd.DataFrame(columns=['prerequisites', 'subsidiaries'])
    metrics = {}
    tokens = 0
    text = ""
    sentPhrase = ""
    sent = []
    appear = []
    section = []
    subsidiaries = []
    sentence = parse(conll)
    metrics['default concepts'] = len(words)
    # Add manual added concept if manual annotation
    if method not in ["1", "2", "3", "4", "5", "6"]:
        new_words = set([])
        rel = Annotations.query.filter_by(bid=bid, cap=cap).all()
        uid = method.split(".")[1]
        for item in rel:
            if (type(item.lemma1) is str):
                get = Annotation_user.query.filter_by(aid=item.aid).first()
                user = User.query.filter_by(uid=get.uid).first()
                new_words.add(item.lemma1.lower())
            elif (type(item.lemma2) is str):
                get = Annotation_user.query.filter_by(aid=item.aid).first()
                user = User.query.filter_by(uid=get.uid).first()
                new_words.add(item.lemma2.lower())
            try:
                int(item.lemma1)
            except ValueError:
                if (Annotation_user.query.filter_by(aid=item.aid).first() and str(Annotation_user.query.filter_by(aid=item.aid).first().uid) == str(uid)):
                    new_words.add(item.lemma1.lower())
            try:
                int(item.lemma2)
            except ValueError:
                if (Annotation_user.query.filter_by(aid=item.aid).first() and str(Annotation_user.query.filter_by(aid=item.aid).first().uid) == str(uid)):
                    new_words.add(item.lemma2.lower())

        metrics['entered concepts'] = len(new_words)
        words.extend(new_words)

    # Prepare sentence and text
    for ids, phrase in enumerate(sentence):
        for word in phrase:
            tokens += 1
            text += lemmatizer.lemmatize(word["form"]) + " "
            sentPhrase += lemmatizer.lemmatize(word["form"]) + " "
        sent.append(sentPhrase)
        sentPhrase = ""

    metrics['tokens'] = tokens
    metrics['sentences'] = len(sentence)
    metrics['strong relations'] = 0
    metrics['weak relations'] = 0
    metrics['unique relations'] = []

    revisione_fatta = False
    if method not in ['1', '2', '3', '4', '5', '6']:
        if Revision_status.query.filter_by(bid=bid, cap=cap, uid=method.split(".")[1]).first().status == "Finished":
            revisione_fatta = True

    for i, word in enumerate(words):
        freq = text.count(word)
        # Check if a word is in a sent
        for k, phrase in enumerate(sent):
            if word in phrase:
                appear.append(k)
        # Check if a word is in a section
        for j, number in enumerate(sentences):
            if (j + 1) < len(sentences):
                if any(phraseId > number.sentence and phraseId < sentences[j + 1].sentence for phraseId in appear):
                    section.append(int(number.section.split(".")[-1]))
            else:
                if any(phraseId > number.sentence for phraseId in appear):
                    section.append(int(number.section.split(".")[-1]))

        # Get all the relationship for baseline methods
        if method in ["1", "2", "3", "4", "5", "6"]:
            subsidiaries = Baseline_Methods.query.filter_by(lemma2=word, bid=bid, cap=cap).all()
            if method == "1":
                subsidiaries = [candidate.lemma1 for candidate in subsidiaries if candidate.m1 == 1]
                for subs in subsidiaries:
                    row = pd.Series({"prerequisites": word, "subsidiaries": subs})
                    dfAnnotation = dfAnnotation.append(row, ignore_index=True)
                    if (word, subs) not in metrics["unique relations"]:
                        metrics["unique relations"].append((word, subs))
            elif method == "2":
                subsidiaries = [candidate.lemma1 for candidate in subsidiaries if candidate.m2 == 1]
                for subs in subsidiaries:
                    row = pd.Series({"prerequisites": word, "subsidiaries": subs})
                    dfAnnotation = dfAnnotation.append(row, ignore_index=True)
                    if (word, subs) not in metrics["unique relations"]:
                        metrics["unique relations"].append((word, subs))
            elif method == "3":
                threshold = Bs_threshold.query.filter_by(bid=bid, cap=cap, method=3).first().threshold
                subsidiaries = [candidate.lemma1 for candidate in subsidiaries if
                                candidate.m3 and (candidate.m3 > threshold)]
                for subs in subsidiaries:
                    #threshold2 = Baseline_Methods.query.filter_by(lemma1=subs, lemma2=word,bid=bid, cap=cap).first().m3
                    row = pd.Series({"prerequisites": word, "subsidiaries": subs})
                    dfAnnotation = dfAnnotation.append(row, ignore_index=True)
                    if (word, subs) not in metrics["unique relations"]:
                        metrics["unique relations"].append((word, subs))
            elif method == "4":
                subsidiaries = [candidate.lemma1 for candidate in subsidiaries if candidate.m4 == 1]
                for subs in subsidiaries:
                    row = pd.Series({"prerequisites": word, "subsidiaries": subs})
                    dfAnnotation = dfAnnotation.append(row, ignore_index=True)
                    if (word, subs) not in metrics["unique relations"]:
                        metrics["unique relations"].append((word, subs))
            elif method == "5":
                threshold = Bs_threshold.query.filter_by(bid=bid, cap=cap, method=5).first().threshold
                subsidiaries = [candidate.lemma1 for candidate in subsidiaries if
                                candidate.m5 and (candidate.m5 > threshold)]
                for subs in subsidiaries:
                    row = pd.Series({"prerequisites": word, "subsidiaries": subs})
                    dfAnnotation = dfAnnotation.append(row, ignore_index=True)
                    if (word, subs) not in metrics["unique relations"]:
                        metrics["unique relations"].append((word, subs))

            elif method == "6":
                # threshold = Bs_threshold.query.filter_by(bid=bid, cap=cap, method=5).first().threshold
                subsidiaries = [candidate.lemma1 for candidate in subsidiaries if
                                candidate.m6 and (candidate.m6 > -3)]
                for subs in subsidiaries:
                    row = pd.Series({"prerequisites": word, "subsidiaries": subs})
                    dfAnnotation = dfAnnotation.append(row, ignore_index=True)
                    if (word, subs) not in metrics["unique relations"]:
                        metrics["unique relations"].append((word, subs))
        # Get relationships for users annotation
        else:
            uid = method.split(".")[1]

            subsidiaries_aid = Annotations.query.filter_by(lemma2=find_term(word), bid=bid, cap=cap).all()
            for candidate in subsidiaries_aid:

                annUsr = Annotation_user.query.filter_by(aid=candidate.aid, uid=uid).first()

                # se revisione è stata fatta e questa relazione è stata revisionata
                if revisione_fatta and Revised_annotations.query.filter_by(ann_user_id=candidate.ann_user_id).first() is not None:
                    # se rev_id = 1 allora la relazione è stata eliminata
                    if Revised_annotations.query.filter_by(ann_user_id=candidate.ann_user_id).first().rev_id == 1:
                        annUsr = None

                if annUsr is not None:
                    peso_cambiato = False
                    # se rev_id = 2 allora il peso è stato cambiato
                    if revisione_fatta and Revised_annotations.query.filter_by(ann_user_id=candidate.ann_user_id).first() is not None:
                        peso_cambiato = Revised_annotations.query.filter_by(ann_user_id=candidate.ann_user_id).first().rev_id == 2

                    if not peso_cambiato:
                        if annUsr.ann_type == 'weak':
                            metrics['weak relations'] += 1
                        elif annUsr.ann_type == 'strong':
                            metrics['strong relations'] += 1
                    else:
                        if annUsr.ann_type == 'strong':
                            metrics['weak relations'] += 1
                        elif annUsr.ann_type == 'weak':
                            metrics['strong relations'] += 1

                    if (candidate.lemma1, candidate.lemma2) not in metrics["unique relations"]:
                        metrics["unique relations"].append((candidate.lemma1, candidate.lemma2))

                    term = Terminology.query.filter_by(tid=candidate.lemma1).first()
                    if (term):
                        term = term.lemma.lower()
                        subsidiaries.append(term)
                    else:
                        term = candidate.lemma1.lower()
                        subsidiaries.append(candidate.lemma1.lower())

                    row = pd.Series({"prerequisites": word.lower(), "subsidiaries": term})
                    dfAnnotation = dfAnnotation.append(row, ignore_index=True)

        row = pd.Series({"ID": i, "name": word, "frequence": freq, "sections": section, "sentence": appear,
                         "subsidiaries": [sub for sub in subsidiaries]})
        df = df.append(row, ignore_index=True)

        appear = []
        section = []
        subsidiaries = []

    return (dfAnnotation, df, metrics, words)

def data_summary(dfAnnotation, df, metrics, method):
    
    """ Takes the two csv to create the metrics for data summary """
    G_nx, G_ig, annotator = create_graphs(dfAnnotation, df, method)
    partial_metrics = compute_metrics(G_nx, G_ig)
    metrics['unique relations'] = len(metrics['unique relations'])
    metrics['transitive'] = detect_transitive_edges(G_nx, 2, find_also_not_inserted=False)
    metrics['transitive'] = len(metrics['transitive']['manually inserted'])
    metrics['loops'] = detect_loops(G_nx, G_ig, df, remove=False)
    if metrics["loops"] is not None:
        metrics['loops'] = len(metrics['loops']['loops'])
    else:
        metrics['loops'] = 0

    #metrics['links'] = partial_metrics['num_edges']
    metrics['links'] = len(dfAnnotation.index)
    metrics['leaves'] = 0

    roots = get_roots(G_nx)
    metrics['roots'] = len(roots)

    # se c'è un ciclo impossibile calcolare longhest path
    try:
        long_path = longest_path(G_nx)

        metrics['logest_path_root'] = long_path[0]
        metrics['logest_path_leaf'] = long_path[-1]
        metrics['logest_path_lenght'] = len(long_path)
    except:
        metrics['logest_path_root'] = "Cycle"
        metrics['logest_path_leaf'] = "Cycle"
        metrics['logest_path_lenght'] = "Cycle"



    for node in G_nx:
        if G_nx.out_degree(node)==0:
            metrics['leaves'] += 1
    
    metrics['diameter'] = partial_metrics['diameter']
    metrics['max out degree'] = partial_metrics['max out degree']
    metrics['max in degree'] = partial_metrics['max in degree']
    
    return(metrics)

def getRelations(bid,cap,rel_id):
    '''se relazioni di utente: rel_id = uid. + id utente
        se relazioni di un baseline method: rel_id = numero metodo
        se relazioni di una gold: rel_id =gold. + id gold

        ritorna lista con elementi (prereq, target, weight) se utente
        ritorna lista con elementi (prereq, target) se baseline method
    '''

    # se è un annotazione di un utente
    if rel_id.startswith('uid'):
        uid = rel_id.split('.')[1]
        relazioni = []

        annotations_id = db.session \
            .query(Annotations.lemma1, Annotations.lemma2, Annotations.aid, Annotation_user.ann_user_id) \
            .join(Annotation_user, (Annotations.aid == Annotation_user.aid)) \
            .filter(Annotations.bid == bid, Annotations.cap == cap,
                    Annotation_user.uid == uid) \
            .all()


        revisione_fatta = Revision_status.query.filter_by(bid=bid, cap=cap, uid=uid).first().status == "Finished"
        # se la revisione è finita ne tengo conto
        if revisione_fatta:
            #elimino le relazioni cancellate nella revisione (rev_id = 1)
            for ann in annotations_id:
                if Revised_annotations.query.filter_by(ann_user_id=ann.ann_user_id).first() is not None:
                    if not Revised_annotations.query.filter_by(ann_user_id=ann.ann_user_id).first().rev_id == 1:
                        annotations_id.remove(ann)

            #annotations_id = [x for x in annotations_id if not Revised_annotations.query.filter_by(aid=x[2]).first().rev_id == 1]


        for ann in annotations_id:
            if type(ann[1]) == int:
                prereq = Terminology.query.filter_by(tid=ann[1]).first().lemma
            else:
                prereq = ann[1]
            if type(ann[0]) == int:
                target = Terminology.query.filter_by(tid=ann[0]).first().lemma
            else:
                target = ann[0]

            weight = Annotation_user.query.filter_by(aid=ann[2],uid=uid).first().ann_type

            #se rev_id = 2 il peso è stato modificato
            if revisione_fatta and Revised_annotations.query.filter_by(ann_user_id=ann[3]).first() is not None:
                if Revised_annotations.query.filter_by(ann_user_id=ann[3]).first().rev_id == 2:
                    if weight == 'strong':
                        weight = 'weak'
                    else:
                        weight = 'strong'

            rel = (prereq, target, weight)
            relazioni.append(rel)
    elif rel_id.startswith("gold"):
        gid = rel_id.split('.')[1]
        relazioni = []
        #TODO

    else:
        # altrimenti metodo di baseline
        if rel_id == '1':
            relazioni = db.session \
                .query(Baseline_Methods.lemma2, Baseline_Methods.lemma1) \
                .filter(Baseline_Methods.bid == bid, Baseline_Methods.cap == cap,
                        Baseline_Methods.m1 == 1) \
                .all()
        elif rel_id == '2':
            relazioni = db.session \
                .query(Baseline_Methods.lemma2, Baseline_Methods.lemma1) \
                .filter(Baseline_Methods.bid == bid, Baseline_Methods.cap == cap,
                        Baseline_Methods.m2 == 1) \
                .all()
        elif rel_id == '3':
            threshold = Bs_threshold.query.filter_by(bid=bid, cap=cap, method=3).first().threshold

            relazioni = db.session \
                .query(Baseline_Methods.lemma2, Baseline_Methods.lemma1) \
                .filter(Baseline_Methods.bid == bid, Baseline_Methods.cap == cap,
                        Baseline_Methods.m3 > threshold) \
                .all()

        elif rel_id == '4':
            relazioni = db.session \
                .query(Baseline_Methods.lemma2, Baseline_Methods.lemma1) \
                .filter(Baseline_Methods.bid == bid, Baseline_Methods.cap == cap,
                        Baseline_Methods.m4 == 1) \
                .all()

        elif rel_id == '5':
            threshold = Bs_threshold.query.filter_by(bid=bid, cap=cap, method=5).first().threshold

            relazioni = db.session \
                .query(Baseline_Methods.lemma2, Baseline_Methods.lemma1) \
                .filter(Baseline_Methods.bid == bid, Baseline_Methods.cap == cap,
                        Baseline_Methods.m5 > threshold) \
                .all()
        elif rel_id == '6':
            threshold = Bs_threshold.query.filter_by(bid=bid, cap=cap, method=6).first().threshold

            relazioni = db.session \
                .query(Baseline_Methods.lemma2, Baseline_Methods.lemma1) \
                .filter(Baseline_Methods.bid == bid, Baseline_Methods.cap == cap,
                        Baseline_Methods.m6 > threshold) \
                .all()

    return relazioni
    
def process_for_matrix(dfAnnotation, df, method, words, namebook):
    """ Takes the two csv to create the table that is required for compute graph analyzer method """
    G_nx, G_ig, annotator = create_graphs(dfAnnotation, df, method)
    partial_metrics = compute_metrics(G_nx, G_ig)
    transitives = detect_transitive_edges(G_nx, 2, find_also_not_inserted=False)
    loops = detect_loops(G_nx, G_ig, df, remove=False)
    memberships = detect_clusters(G_ig)
    dfMatrix = pd.DataFrame(index = [name for name in words], columns = [name for name in words])
    dfMatrix = dfMatrix.fillna(0)
    for row in df.itertuples():
        name = row.name
        relations = dfAnnotation.loc[dfAnnotation.prerequisites == name, 'subsidiaries'].tolist()
        for word in relations:
            if type(dfMatrix.loc[name, word]) is list:
                dfMatrix.loc[name, word] = dfMatrix.loc[name, word].append(method)
            else:
                dfMatrix.loc[name, word] = [method]

    if "uid" in method:
        numeroutente = method.split(".")
        nomeutente = User.query.filter_by(uid=numeroutente[1]).first()
        utente = method + "." + nomeutente.name + " " + nomeutente.surname
        final = create_graph_dict(df, dfMatrix, utente, partial_metrics, loops, transitives, memberships, G_nx)
        final["__comment__"] = namebook
        final = json.dumps(final, indent=4,
                           sort_keys=True,
                           separators=(',', ': '))
    else:
        print("entrato1")
        final = create_graph_dict(df, dfMatrix, method, partial_metrics, loops, transitives, memberships, G_nx)
        final["__comment__"] = namebook
        final = json.dumps(final, indent=4,
                                 sort_keys=True,
                                 separators=(',', ': '))  
    return(final)

def process_for_matrix_gold(dfAnnotation, df, method, words,namebook):
    """ Takes the two csv to create the table for the gold standard that is required for compute graph analyzer method """
    G_nx, G_ig, annotator = create_graphs(dfAnnotation, df, method)
    partial_metrics = compute_metrics(G_nx, G_ig)
    transitives = detect_transitive_edges(G_nx, 2, find_also_not_inserted=False)
    loops = detect_loops(G_nx, G_ig, df, remove=False)
    memberships = detect_clusters(G_ig)

    uids = goldStandard.query.filter_by(gid=method.split(".")[1]).first().uids
    listaUids = uids.split(" ")
    listaUids = [uid for uid in listaUids if uid]
    listautenti=[]
    for uid in listaUids:
        lista = uid.split(".")
        nomeutenti= User.query.filter_by(uid=lista[1]).first()
        utente = lista[1] + "."+ nomeutenti.name+" "+nomeutenti.surname
        listautenti.append(utente)
    for index, row in df.iterrows():
        name = row["name"]
        if name not in words:
            words.append(name)
    dfMatrix = pd.DataFrame(index = [name for name in words], columns = [name for name in words])
    dfMatrix = dfMatrix.fillna(0)
    for index, row in df.iterrows():
        name = row["name"]
        for uid in listaUids:
            if not pd.isna(row[uid]):
                wordsList = ast.literal_eval(row[uid])
                for word in wordsList:
                    if type(dfMatrix.loc[name, word]) is str:
                        dfMatrix.loc[name, word] = dfMatrix.loc[name, word] + " "+ uid
                    else:
                        dfMatrix.loc[name, word] = [uid]

                                   

    final = create_graph_dict(df, dfMatrix, listautenti, partial_metrics, loops, transitives, memberships, G_nx)
    final["__comment__"] = namebook
    

    
    final = json.dumps(final, indent=4,
                                 sort_keys=True,
                                 separators=(',', ': ')) 
    
    return(final)
    
    
def processConll(conll, bid):
    """ Process and save the conll as is required by the conll_processor module"""    
    
    df = pd.DataFrame(columns=['doc_id', 'paragraph_id', 'sentence_id', 'sentence', 'token_id', 'token', 'lemma', 'upos', 'xpos', 'feats', 'head_token_id', 'dep_rel', 'deps', 'misc'])  
    conll = re.sub(r"\t", " ", conll)
    lines = conll.splitlines()
    stop_paragraph = '# newpar'
    stop_sent = '# sent_id'
    paragraph = 0
    sent_id = 0
    for line in lines[1:]:
        if line == stop_paragraph:
            paragraph += 1
            continue
        if line.startswith(stop_sent):
            sent_id += 1
            continue
        if line.startswith('# text'):
            text = line.split('= ', 1)[1]
            continue
        if not line:
            continue
        
        elements = line.split()
        token_id, token, lemma, upos, xpos, feats, head_token_id, dep_rel, deps, misc = [item for item in elements] 
        
        row = pd.Series({'doc_id': bid, 'paragraph_id': paragraph, 'sentence_id': sent_id, 'sentence': text, 'token_id': token_id, 'token': token, 'lemma': lemma, 'upos':upos, 'xpos': xpos, 'feats': feats, 'head_token_id': head_token_id, 'dep_rel': dep_rel, 'deps': deps, 'misc': misc})
        df = df.append(row, ignore_index=True)
    return df.to_csv()

def conll_annotation(conll):
    final_conll = []
    conll = re.sub(r"\t", " ", conll)
    lines = conll.splitlines()
    stop_paragraph = '# newpar'
    stop_sent = '# sent_id'
    sent_id = 0
    tok_id = 0
    
    for line in lines[1:]:
        if line == stop_paragraph:
            continue
        if line.startswith(stop_sent):
            sent_id += 1
            continue
        if line.startswith('# text'):
            continue
        if not line:
            continue
        
        tok_id += 1
        elements = line.split()
        token_id, token, lemma, upos, xpos, feats, head_token_id, dep_rel, deps, misc = [item for item in elements] 
        
        data = {}
    
        data['tok_id'] = tok_id
        data['sent_id'] = sent_id
        data['pos_in_sent'] = str(token_id)
        data['forma'] = token
        data['lemma'] = lemma
        data['pos_coarse'] = upos
        data['pos_fine'] = xpos
        data['iob'] = '_'
        data['part_of_concept'] = ''
        final_conll.append(data)
        
    return final_conll
    
def upload_Annotation(json, bid, cap, uid):
    """ Takes the json and create the rows that will be saved in the database """
    
    types = Annotation_types.query.all()
    dictionary = {}
    for item in types:
        dictionary[item.ann_type] = item.tid
        
    for item in json["savedInsertedRelations"]:
        lemma1 = find_term(item["advanced"])
        if not (Terminology_reference.query.filter_by(tid=lemma1, bid=bid,cap=cap).first()):
            lemma1 = item["advanced"].upper()
        lemma2 = find_term(item["prerequisite"])
        if not (Terminology_reference.query.filter_by(tid=lemma2, bid=bid, cap=cap).first()):
            lemma2 = item["prerequisite"].upper()
        id_phrase = item["sent"]
        weight = item["weight"]
        annotationObj = Annotations.query.filter_by(bid=bid, cap=cap, lemma1=lemma1, lemma2=lemma2).first()
        if (annotationObj):
            aid = annotationObj.aid
            annotationUserObj = Annotation_user.query.filter_by(uid=uid, aid=aid, ann_type=weight).first()
            #if(annotationUserObj is None):
            db.session.add(Annotation_user(uid=uid, aid=aid, ann_type=weight))
        else:
            annotationObj = Annotations(bid=bid, cap=cap, lemma1=lemma1, lemma2=lemma2, id_phrase=id_phrase)
            db.session.add(annotationObj)
            db.session.commit()
            aid = Annotations.query.filter_by(bid=bid, cap=cap, lemma1=lemma1, lemma2=lemma2, id_phrase=id_phrase).first().aid

            annotationUserObj = Annotation_user.query.filter_by(uid=uid, aid=aid, ann_type=weight).first()
            if (annotationUserObj is None):
                db.session.add(Annotation_user(uid=uid, aid=aid, ann_type=weight))
    db.session.commit()
    
def create_dfAnnotation(bid, cap, gid, conll, words):
    """ Create the dfAnnotation and df tables starting from conll """
    metrics = {}
    metrics['strong relations'] = 0
    metrics['weak relations'] = 0
    metrics['unique relations'] = []
    sentence = parse(conll)
    metrics['default concepts'] = len(words)
    tokens = 0 
    gold_standard = goldStandard.query.filter_by(gid=gid.split(".")[1]).first().gold
    uids = goldStandard.query.filter_by(gid=gid.split(".")[1]).first().uids
    listaUids = uids.split(" ")
    listaUids = [uid for uid in listaUids if uid]
        
    
    df = pd.read_csv(pd.compat.StringIO(gold_standard))    
    #print(df.name)
    new_words = set([])
    dfAnnotation = get_df_gold(gid.split(".")[1])

    
    for row in dfAnnotation.itertuples():
        lemma1 = find_term(row.subsidiaries)
        if type(lemma1) == int:
            term = Terminology_reference.query.filter_by(tid=lemma1, cap=cap, bid=bid).first()
            if not term:
                lemma1 = row.subsidiaries.upper()
        lemma2 = find_term(row.prerequisites)
        if type(lemma2) == int:
            term = Terminology_reference.query.filter_by(tid=lemma2, cap=cap, bid=bid).first()
            if not term:
                lemma2 = row.prerequisites.upper()

        strong_rels = []
        weak_rels = []
        
        aids = Annotations.query.filter_by(lemma1=lemma1, lemma2=lemma2, bid=bid, cap=cap).all()
        for uid in listaUids:
            for aid in aids:
                annType = Annotation_user.query.filter_by(aid=aid.aid, uid=uid.split(".")[1]).first()
                if(annType):
                    annType = annType.ann_type
                    if annType == "weak":
                        if str(lemma2) + "-" + str(lemma1) not in weak_rels:
                            metrics['weak relations'] += 1
                            weak_rels.append(str(lemma2) + "-" + str(lemma1))

                    elif annType == "strong":
                        if str(lemma2) + "-" + str(lemma1) not in strong_rels:
                            metrics['strong relations'] += 1
                            strong_rels.append(str(lemma2) + "-" + str(lemma1))

                    if (row.subsidiaries, row.prerequisites) not in metrics["unique relations"]:
                        metrics["unique relations"].append((row.subsidiaries, row.prerequisites))
                        """ Modifico dfAnnotation con il rispettivo peso """
                        for index in dfAnnotation.index:
                            if dfAnnotation.loc[index, 'prerequisites'] ==  row.prerequisites and dfAnnotation.loc[index, 'subsidiaries'] == row.subsidiaries:
                                dfAnnotation.loc[index,'weight'] = annType



    for row in df.itertuples():
        lemma1 = find_term(row.name)
        #print(row.name + '---->' + str(lemma1))
        if type(lemma1) == int:
            term = Terminology_reference.query.filter_by(tid=lemma1, cap=cap, bid=bid).first()
            if not term:
                #if (dfAnnotation['prerequisites'] == row.name).any():
                if (dfAnnotation['prerequisites'] == row.name).any() or (dfAnnotation['subsidiaries'] == row.name).any():
                    new_words.add(row.name.lower())
        else:
            #if (dfAnnotation['prerequisites'] == row.name).any():
            if (dfAnnotation['prerequisites'] == row.name).any() or (dfAnnotation['subsidiaries'] == row.name).any():
                new_words.add(row.name.lower())
    
    
    for ids, phrase in enumerate(sentence):
        for word in phrase:
            tokens += 1
            
    metrics['tokens'] = tokens
    metrics['sentences'] = len(sentence)
    metrics['entered concepts'] = len(new_words)
    
    words.extend(new_words)
    
    return dfAnnotation, df, metrics, words
    
    
def create_gold(uids, bid, cap, words, conll, sentences,agreeement):
    """ Create df table for a gold """
    lemmatizer = WordNetLemmatizer()
    text = ""
    sentPhrase = ""
    sent = []
    appear = []
    section = []
    sentence = parse(conll)
    new_words = set([])
    rel = Annotations.query.filter_by(bid=bid, cap=cap).all()



    for uid in uids:
        uid = uid.split('.')[1]
        for item in rel:
            try:
                int(item.lemma1)
            except ValueError:
                if (Annotation_user.query.filter_by(aid=item.aid).first() and str(Annotation_user.query.filter_by(aid=item.aid).first().uid) == str(uid)):
                    new_words.add(item.lemma1.lower())
                elif item.lemma1.lower() not in words and item.lemma1.lower() not in new_words :
                    new_words.add(item.lemma1.lower())
            try:
                int(item.lemma2)
            except ValueError:
                if (Annotation_user.query.filter_by(aid=item.aid).first() and str(Annotation_user.query.filter_by(aid=item.aid).first().uid) == str(uid)):
                    new_words.add(item.lemma2.lower())
                elif item.lemma2.lower() not in words and item.lemma2.lower() not in new_words :
                    new_words.add(item.lemma2.lower())



    words.extend(new_words)
    df = pd.DataFrame(columns=['ID', 'name', 'frequence', 'sections', 'sentence'])

    for uid in uids:
        df[uid] = ""
    
    for ids, phrase in enumerate(sentence):
        for word in phrase:
            text += lemmatizer.lemmatize(word["form"]) + " "
            sentPhrase += lemmatizer.lemmatize(word["form"]) + " "
        sent.append(sentPhrase)
        sentPhrase = ""
      
    for i, word in enumerate(words):

        dictionary = {}
        freq = text.count(word)
        # Check if a word is in a sent
        for k, phrase in enumerate(sent):
            if word in phrase:
                appear.append(k)

        # Check if a word is in a section
        for j, number in enumerate(sentences):
            if (j + 1) < len(sentences):
                if any(phraseId > number.sentence and phraseId < sentences[j+1].sentence for phraseId in appear):
                    section.append(int(number.section.split(".")[-1]))
            else:
                if any(phraseId > number.sentence for phraseId in appear):
                    section.append(int(number.section.split(".")[-1]))

        for uid in uids:
            name = uid
            uid = uid.split(".")[1]
            lemma2 = find_term(word)
            if type(lemma2) == int:
                term = Terminology_reference.query.filter_by(tid=lemma2, cap=cap, bid=bid).first()
                if not term:
                    lemma2 = word.upper()
            subsidiaries_aid = Annotations.query.filter_by(lemma2=lemma2, bid=bid, cap=cap).all()
            temp = []
            for candidate in subsidiaries_aid:
                annUsr = Annotation_user.query.filter_by(aid=candidate.aid, uid=uid).first()
                if annUsr:
                    for candidate in subsidiaries_aid:
                        if Annotation_user.query.filter_by(aid=candidate.aid, uid=uid).first():
                            term = Terminology.query.filter_by(tid = candidate.lemma1).first()
                            if term:
                                if term.lemma.lower() not in temp:
                                    temp.append(term.lemma.lower())

                            elif candidate.lemma1.lower() not in temp:
                                temp.append(candidate.lemma1.lower())

            dictionary[name] = temp
            
        row = pd.Series({"ID": i, "name": word, "frequence": freq, "sections": section, "sentence": appear})
        df = df.append(row, ignore_index=True)
        
        appear = []
        section = []

        if dictionary:
            for uid in uids:
                try:
                    df.iloc[-1, df.columns.get_loc(uid)] = dictionary[uid]
                except:
                    pass

    return df.to_csv()


def get_df_gold(gid):

    gold = goldStandard.query.filter_by(gid=gid).first()

    gold_csv = gold.gold

    uids = gold.uids
    listaUids = uids.split(" ")
    listaUids = [uid for uid in listaUids if uid]

    # agreement dice quanti utenti devono aver messo la relazione per essere inserita nella gold
    agreement = gold.agreements
    # se la relazione è stata messa da tot utenti allora va inserita nella gold
    utenti_min = 1

    if agreement is not None and agreement != "0%":
        agreement = int(agreement.replace('%', ''))
        utenti_min = round(agreement * (len(listaUids)) / 100)

    df_csv = pd.read_csv(pd.compat.StringIO(gold_csv))

    df_gold = pd.DataFrame(columns=['prerequisites', 'subsidiaries'])

    #count quanti utenti hanno messo la relazioni
    count_rels = {}

    for index, row in df_csv.iterrows():
        for uid in listaUids:

            wordsList = ast.literal_eval(df_csv.iloc[index][uid])
            name = df_csv.iloc[index]["name"]

            for word in wordsList:

                rel = name+'_'+word

                if count_rels.get(rel) is None:
                    count_rels[rel] = 1
                else:
                    count_rels[rel] += 1

                if count_rels[rel] == utenti_min and not ((df_gold['prerequisites'] == name) & (df_gold['subsidiaries'] == word)).any():
                    row = pd.Series({"prerequisites": name, "subsidiaries": word})
                    df_gold = df_gold.append(row, ignore_index=True)

    return df_gold
    
def find_term(lemma):
    lemmaObj = Terminology.query.filter_by(lemma=lemma.lower()).first()
    if (lemmaObj):
        return lemmaObj.tid
    else:
        return lemma.upper()
            
        
def agreement_json(bid, cap, uid):
    dict_list = []
    ann_list = Annotations.query.filter_by(bid=bid, cap=cap).all()

    # se la revisione è stata fatta cancello le relazioni eliminate
    if Revision_status.query.filter_by(bid=bid, cap=cap, uid=uid).first().status == "Finished":
        for ann in ann_list:
            # se rev_id = 1 allora la relazione è stata eliminata
            annUsr = Annotation_user.query.filter_by(aid=ann.aid, uid=uid).all()

            for a in annUsr:
                revision = Revised_annotations.query.filter_by(ann_user_id=a.ann_user_id).first()
                if revision:
                    if revision.rev_id == 1:
                        ann_list.remove(ann)

    for item in ann_list:
        dictionary = {}
        ann = Annotation_user.query.filter_by(uid=uid, aid=item.aid).first()
        if(ann):
            dictionary["sent"] = item.id_phrase
            
            if(type(item.lemma1) == int):
                dictionary["advanced"] = Terminology.query.filter_by(tid = item.lemma1).first().lemma
            else:
                dictionary["advanced"] = item.lemma1
                
            if(type(item.lemma2) == int):
                dictionary["prerequisite"] = Terminology.query.filter_by(tid = item.lemma2).first().lemma
            else:
                dictionary["prerequisite"] = item.lemma2

            peso_cambiato = False
            # Se la revisione è stata fatta e il peso è stato cambiato, cambio il peso
            if Revision_status.query.filter_by(bid=bid, cap=cap, uid=uid).first().status == "Finished":
                annUsr = Annotation_user.query.filter_by(aid=ann.aid, uid=uid).all()
                for a in annUsr:
                    if Revised_annotations.query.filter_by(ann_user_id=a.ann_user_id).first():
                        if Revised_annotations.query.filter_by(ann_user_id=a.ann_user_id).first().rev_id == 2:
                            peso_cambiato = True
                            if ann.ann_type == "strong":
                                dictionary["weight"] = "weak"
                            else:
                                dictionary["weight"] = "strong"

            if not peso_cambiato:
                dictionary["weight"] = ann.ann_type
            
            dict_list.append(dictionary)
        
    return dict_list


def linguistic_json(bid, cap, uid):
    dict_list = []
    ann_list = Annotations.query.filter_by(bid=bid, cap=cap).all()

    # se la revisione è stata fatta cancello le relazioni eliminate
    if Revision_status.query.filter_by(bid=bid, cap=cap, uid=uid).first().status == "Finished":
        for ann in ann_list:
            # se rev_id = 1 allora la relazione è stata eliminata
            annUsr = Annotation_user.query.filter_by(aid=ann.aid, uid=uid).all()
            for a in annUsr:
                revision = Revised_annotations.query.filter_by(ann_user_id=a.ann_user_id).first()
                if revision:
                    if revision.rev_id == 1:
                        ann_list.remove(ann)

    for item in ann_list:
        dictionary = {}
        ann = Annotation_user.query.filter_by(uid=uid, aid=item.aid).first()
        if (ann):
            dictionary["sent"] = item.id_phrase

            if (type(item.lemma1) == int):
                dictionary["advanced"] = Terminology.query.filter_by(tid=item.lemma1).first().lemma
            else:
                dictionary["advanced"] = item.lemma1

            if (type(item.lemma2) == int):
                dictionary["prerequisite"] = Terminology.query.filter_by(tid=item.lemma2).first().lemma
            else:
                dictionary["prerequisite"] = item.lemma2

            peso_cambiato = False
            # Se la revisione è stata fatta e il peso è stato cambiato, cambio il peso
            if Revision_status.query.filter_by(bid=bid, cap=cap, uid=uid).first().status == "Finished":
                annUsr = Annotation_user.query.filter_by(aid=ann.aid, uid=uid).all()
                for a in annUsr:
                    if Revised_annotations.query.filter_by(ann_user_id=a.ann_user_id).first():
                        if Revised_annotations.query.filter_by(ann_user_id=a.ann_user_id).first().rev_id == 2:
                            peso_cambiato = True
                            if ann.ann_type == "strong":
                                dictionary["weight"] = "weak"
                            else:
                                dictionary["weight"] = "strong"

            if not peso_cambiato:
                dictionary["weight"] = ann.ann_type

            dict_list.append(dictionary)
    final = {}
    final["savedInsertedRelations"] = dict_list

    return final


def linguistic_json_gold(bid, cap, gid):
    dict_list = []

    uids = goldStandard.query.filter_by(gid=gid).first().uids
    listaUids = uids.split(" ")
    listaUids = [uid for uid in listaUids if uid]

    dfAnnotation = get_df_gold(gid)

    for row in dfAnnotation.itertuples():
        dictionary = {}
        lemma1 = find_term(row.subsidiaries)
        lemma2 = find_term(row.prerequisites)

        dictionary["advanced"] = row.subsidiaries
        dictionary["prerequisite"] = row.prerequisites

        aids = Annotations.query.filter_by(lemma1=lemma1, lemma2=lemma2, bid=bid, cap=cap).all()
        for uid in listaUids:
            for aid in aids:
                dictionary["sent"] = aid.id_phrase
                annType = Annotation_user.query.filter_by(aid=aid.aid, uid=uid.split(".")[1]).first()

                if (annType):
                    dictionary["weight"] = annType.ann_type

                if dictionary not in dict_list:
                    dict_list.append(dictionary)

    final = {}
    final["savedInsertedRelations"] = dict_list

    return final

def linguistic_json_method2(bid, cap):
    dict_list = []

    relations = Baseline_Methods.query.filter_by(bid=bid, cap=cap, m2=1)
    for rel in relations:
        dictionary = {}
        dictionary["prerequisite"] = rel.lemma2
        dictionary["advanced"] = rel.lemma1
        dictionary["sent"] = rel.m2_sentence

        dict_list.append(dictionary)

    final = {}
    final["savedInsertedRelations"] = dict_list

    return final

# Calcola accuracy precision recall F1 score rispetto ad una gold
def scores(bid, cap, dfAnnotation_method, dfAnnotation_Gold, method):

    # relazioni non trovate dal metodo
    if method == "1":
        method_negative_relations = Baseline_Methods.query.filter_by(bid=bid, cap=cap, m1=0)
    elif method == "2":
        method_negative_relations = Baseline_Methods.query.filter_by(bid=bid, cap=cap, m2=0)
    elif method == "3":
        threshold = Bs_threshold.query.filter_by(bid=bid, cap=cap, method=3).first().threshold
        method_negative_relations = Baseline_Methods.query.filter(bid == bid, cap == cap,
                                                                  Baseline_Methods.m3 <= threshold)
    elif method == "4":
        method_negative_relations = Baseline_Methods.query.filter_by(bid=bid, cap=cap, m4=0)
    elif method == "5":
        threshold = Bs_threshold.query.filter_by(bid=bid, cap=cap, method=5).first().threshold
        method_negative_relations = Baseline_Methods.query.filter(bid == bid, cap == cap,
                                                                  Baseline_Methods.m5 <= threshold)
    elif method == "6":
        threshold = Bs_threshold.query.filter_by(bid=bid, cap=cap, method=6).first().threshold
        method_negative_relations = Baseline_Methods.query.filter(bid == bid, cap == cap, Baseline_Methods.m6 <= threshold)

    TP = 0
    TN = 0
    FP = 0
    FN = 0

    for row in dfAnnotation_method.itertuples():
        rel = (row.prerequisites, row.subsidiaries)
        isin = False
        for row_gold in dfAnnotation_Gold.itertuples():
            rel_gold = (row_gold.prerequisites, row_gold.subsidiaries)
            if rel == rel_gold:
                isin = True
                TP += 1
                break

        if not isin:
            FP += 1

    for row in method_negative_relations:
        rel = (row.lemma2, row.lemma1)
        isin = False
        for row_gold in dfAnnotation_Gold.itertuples():
            rel_gold = (row_gold.prerequisites, row_gold.subsidiaries)
            if rel == rel_gold:
                isin = True
                FN += 1
                break

        if not isin:
            TN += 1

    accuracy = (TP + TN) / (TP + TN + FP + FN)

    if TP + FP != 0:
        precision = TP / (TP + FP)
    else:
        precision = 0


    if TP + TN != 0:
        recall = TP / (TP + FN)
    else:
        recall = 0

    if precision != 0 or recall != 0:
        F1 = 2 * (precision * recall) / (precision + recall)
    else:
        F1 = 0.0
    
    return round(accuracy,3), round(precision,3), round(recall,3), round(F1,3)


def get_list_annotations(bid,cap):

    annotationList = []

    # Get users annotation
    annotationRel = Annotations.query.filter_by(cap=cap, bid=bid).all()
    users = []
    for annotations in annotationRel:
        userz = Annotation_user.query.filter_by(aid=annotations.aid).all()
        for user in userz:
            user = user.uid
            if user and user not in users:
                users.append(user)
                annotationObj = {}
                annotationObj["id"] = "uid." + str(user)
                annotationObj["name"] = "Annotation of: " + str(
                    User.query.filter_by(uid=user).first().name) + " " + str(
                    User.query.filter_by(uid=user).first().surname)
                annotationList.append(annotationObj)

    # Get gold annotation
    annotationGold = goldStandard.query.filter_by(cap=cap, bid=bid).first()


    #for item in annotationGold:
    if annotationGold:
        nomeGold = annotationGold.name
        annotationObj = {}
        annotationObj["id"] = "gold." + str(annotationGold.gid)
        annotationObj["name"] = str(nomeGold)
        annotationList.append(annotationObj)

    methods = Bs_status.query.filter_by(cap=cap, bid=bid).all()

    succ_methods = []
    for m in methods:
        if m.status =="succeeded" or m.status == "modifiable":
            succ_methods.append(m.method)

    # Get baseline
    if succ_methods:
        if 1 in succ_methods:
            annotationObj = {}
            annotationObj["id"] = 1
            annotationObj["name"] = "1: Lexical Relations"
            annotationList.append(annotationObj)
        if 2 in succ_methods:
            annotationObj = {}
            annotationObj["id"] = 2
            annotationObj["name"] = "2: Lexical Syntactic Pattern Match"
            annotationList.append(annotationObj)
        if 3 in succ_methods:
            annotationObj = {}
            annotationObj["id"] = 3
            annotationObj["name"] = "3: Relational Metric"
            annotationList.append(annotationObj)
        if 4 in succ_methods:
            annotationObj = {}
            annotationObj["id"] = 4
            annotationObj["name"] = "4: Wikipedia"
            annotationList.append(annotationObj)
        if 5 in succ_methods:
            annotationObj = {}
            annotationObj["id"] = 5
            annotationObj["name"] = "5: Textbook Structure"
            annotationList.append(annotationObj)
        if 6 in succ_methods:
            annotationObj = {}
            annotationObj["id"] = 6
            annotationObj["name"] = "6: Temporal Patterns"
            annotationList.append(annotationObj)

    return annotationList