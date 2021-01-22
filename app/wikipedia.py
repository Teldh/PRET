# -*- coding: utf-8 -*-

import wikipedia
import nltk
import string
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re, math
from collections import Counter
from app import app, db
from app.models import Terminology, Terminology_reference
from time import sleep
import requests

WORD = re.compile(r'\w+')

def tokenizeContent(contentsRaw):
    tokenized = nltk.tokenize.word_tokenize(contentsRaw)
    return tokenized

def removeStopWordsFromTokenized(contentsTokenized):
    stop_word_set = set(nltk.corpus.stopwords.words('english'))
    filteredContents = [word for word in contentsTokenized if word not in stop_word_set]
    return filteredContents

def performPorterStemmingOnContents(contentsTokenized):
    porterStemmer = nltk.stem.PorterStemmer()
    filteredContents = [porterStemmer.stem(word) for word in contentsTokenized]
    return filteredContents

def removePunctuationFromTokenized(contentsTokenized):
    excludePuncuation = set(string.punctuation)
    
    # manually add additional punctuation to remove
    doubleSingleQuote = '\'\''
    doubleDash = '--'
    doubleTick = '``'

    excludePuncuation.add(doubleSingleQuote)
    excludePuncuation.add(doubleDash)
    excludePuncuation.add(doubleTick)

    filteredContents = [word for word in contentsTokenized if word not in excludePuncuation]
    return filteredContents

def convertItemsToLower(contentsRaw):
    filteredContents = [term.lower() for term in contentsRaw]
    return filteredContents

def processData(rawContents):
    cleaned = tokenizeContent(rawContents)
    cleaned = removeStopWordsFromTokenized(cleaned)
    cleaned = performPorterStemmingOnContents(cleaned)    
    cleaned = removePunctuationFromTokenized(cleaned)
    cleaned = convertItemsToLower(cleaned)
    return cleaned

def calc_and_print_CosineSimilarity_for_all(tfs, text):
    numValue = cosine_similarity(tfs[0], tfs[1])
    #print(numValue, end='\t')
    return (numValue[0][0])
    #(cosine_similarity(tfs[i], tfs[n]))[0][0]
    
    
def get_cosine(vec1, vec2):
     intersection = set(vec1.keys()) & set(vec2.keys())
     numerator = sum([vec1[x] * vec2[x] for x in intersection])

     sum1 = sum([vec1[x]**2 for x in vec1.keys()])
     sum2 = sum([vec2[x]**2 for x in vec2.keys()])
     denominator = math.sqrt(sum1) * math.sqrt(sum2)

     if not denominator:
        return 0.0
     else:
        return float(numerator) / denominator

def text_to_vector(text):
     words = WORD.findall(text)
     return Counter(words)

def page_finder(concept, rawContentDict, bid, cap):
    
    flag = False
    best = 0
    right_page = None
    try:
        poss = wikipedia.page(concept)
        term = Terminology(lemma=concept.lower(), wiki_url=poss.title)
    except wikipedia.exceptions.DisambiguationError as e:
        for i, page in enumerate(e.options):
            try:
                poss = wikipedia.page(page)
                print(poss.title)
                rawContentDict["text2"] = poss.summary    
                text = [rawContentDict["text1"], rawContentDict["text2"]]
                tfidf = TfidfVectorizer(tokenizer=processData, stop_words="english")
                tfs = tfidf.fit_transform(rawContentDict.values())
                current = calc_and_print_CosineSimilarity_for_all(tfs, text)
                if current > best:
                    best = current
                    right_page = poss
#                if best > 0.1:
#                    break
    #            if current1 > best1:
    #                best1 = current1
    #                right_page1 = poss
            except wikipedia.exceptions.DisambiguationError as e:
                pass
            except wikipedia.exceptions.PageError as e:
                pass
        term = Terminology(lemma=concept.lower(), wiki_url=right_page.title)
    except wikipedia.exceptions.PageError as e:
        flag = True
    
    if(not flag):
        print(term.wiki_url)
        if Terminology.query.filter_by(lemma=term.lemma, wiki_url = term.wiki_url).first() is None:
            db.session.add(term)
            db.session.flush()

            if not(Terminology_reference.query.filter_by(tid=term.tid, cap=cap, bid=bid).first()):
                term_ref = Terminology_reference(tid=term.tid, cap=cap, bid=bid)
                db.session.add(term_ref)
        else:
            tid = Terminology.query.filter_by(lemma=term.lemma, wiki_url = term.wiki_url).first().tid
            if not (Terminology_reference.query.filter_by(tid=tid, cap=cap, bid=bid).first()):
                term_ref = Terminology_reference(tid=tid, cap=cap, bid=bid)
                db.session.add(term_ref)


def initialize_page(text, words, bid, cap):

    rawContentDict = {"text1": text}
    for concept in words:
        try:
            #if not Terminology.query.filter_by(lemma = concept.lower()).first(): #disambiguazione va fatta sempre
            page_finder(concept, rawContentDict, bid, cap)

        except requests.exceptions.RequestException as e:
            #troppe richieste insieme a wikipedia, mi fermo e riprovo
            sleep(5)
            continue
    db.session.commit()
        

        
