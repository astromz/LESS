# -*- coding: utf-8 -*-
"""
Load in a given article and calculate its similarity score.

Created on Thu Sep 17 12:17:44 2015
@author: mxz20
"""

from __future__ import print_function
#import numpy as np
import os
from gensim import corpora, models, similarities
import re
from nltk import word_tokenize, WordNetLemmatizer
from nltk.corpus import stopwords
from textstat.textstat import textstat
from pandas import DataFrame
from numpy import arange,array


cwd = os.getcwd()
path =cwd + '/app/models/'


def word_difficulty(tfidf_prob, words):
    
    #split bigrams
    df = DataFrame(tfidf_prob, words, columns=['prob','word'])
    splitted=[]
    split_probs=[]
    unigram=[]
    probs=[]
    for w,prob in zip(words, tfidf_prob):
        if '_' in w:
            splitted = splitted + w.split('_')
            split_probs= split_probs + [prob, prob]
        else:
            unigram.append(w)   
            probs.append(prob)
    all_words= unigram + splitted
    all_prob = array(probs + split_probs)
    
    word_len = array([len(w) for w in all_words])
    
    # Dtermine joint difficulty+tfidf of words
    syllable_cnt =  array([textstat.syllable_count(w) for w in all_words])   
    difficulty = all_prob*2 * word_len  * (syllable_cnt**2)
    
    #import pdb;pdb.set_trace()
    df = DataFrame(columns=['word','difficulty','prob','syllable','word_len'])
    df.word=all_words
    df.difficulty = difficulty
    df.prob=all_prob
    df.word_len=word_len
    df.syllable=syllable_cnt
    df.sort(columns='difficulty', ascending=False,inplace=True)
    df.index = arange(len(df))
    return df


#%%

def doc_loader(text, category='science',n_topics=100,
               query_only=False, get_word_rank=False, word_rank_only=False):
    '''Processe input text and transform it into results for web app.
    '''

    category=category.title() 
    if category=='Technology':
        no_below=20
        no_above=0.3
    elif category=='Environment':
        no_below=30
        no_above=0.3
    else:
        no_below=20
        no_above=0.1
        
    
    wnl = WordNetLemmatizer()    
    sw = stopwords.words('english')
        
    #Preprocessing
    text=re.sub('[^a-zA-Z0-9,_-]',' ', text)
    tokens = word_tokenize(text)
    #print(line+'\n')
    
    #remove non-letters at the end
    tokens=[re.sub('[^a-zA-Z0-9]{1,5}$', ' ', t) for t in tokens]
    # remove non-letters at the front
    tokens=[re.sub('^[^a-zA-Z0-9]{1,5}', ' ', t) for t in tokens]
    
    tokens = [w.lower() for w in tokens]
    tokens = [wnl.lemmatize(w,pos='n') for w in tokens] #lemmatize verb
    tokens = [wnl.lemmatize(w,pos='v') for w in tokens] #lemmatize verb
    tokens = [wnl.lemmatize(w,pos='a') for w in tokens] #lemmatice adj
    tokens = [wnl.lemmatize(w,pos='r') for w in tokens] #lemmatize adv
    tokens = [wnl.lemmatize(w,pos='s') for w in tokens] #lemmatize adv-sat
    tokens = [w for w in tokens if w not in sw] # remove stop words
        


#%%    
    
    # Loaded in trigram transformation model
    trigram=models.Phrases.load(path+'trigram_model_{}.pickle'.format(category))
    doc_trigram = trigram[tokens] # transform to trigrams

    # refine the words again -- remove single syllable words and those <3 letters
    doc_trigram = [t for t in doc_trigram if ((len(t)>2) or ('_' in t) ) ]
    #doc_trigram = [t for t in doc_trigram if (textstat.syllable_count(t)>=2 or ('_' in t))]            
    
    
    # vectorize using bag of words using stored dictionary
    dictionary = corpora.Dictionary.load(path+'less_{0}_nobelow{1}_noabove{2}.dict'.format(category, no_below, no_above))
    doc_vectorized = dictionary.doc2bow(doc_trigram)
    
    
    if get_word_rank:
        #Load tfidf transformation model
        tfidf=models.TfidfModel.load(path+'tfidf_model_{0}_nobelow{1}_noabove{2}.pickle'.format(category,no_below, no_above))
        doc_tfidf = tfidf[doc_vectorized]
    
        # Now determine the difficulty levels of words in text with probability
        doc_tfidf_pd=DataFrame(doc_tfidf, columns=['tokenid','prob'])
        doc_tfidf_pd.sort(columns='prob',ascending=False, inplace=True)
        doc_tfidf_pd.index = arange(0,len(doc_tfidf_pd))
        words =[dictionary.get(tid) for tid in doc_tfidf_pd.tokenid]
        word_level=word_difficulty(doc_tfidf_pd.prob, words)
        if word_rank_only:
            return word_level
    
    
    # Now Load trained LDA model
    lda_model = models.ldamodel.LdaModel.load(path+'lda_model_{0}_{1}_nobelow{2}_noabove{3}.pickle'.format(category, n_topics, no_below, no_above))
    doc_lda = lda_model[doc_vectorized] #infer topic distributions on new documents
    
    
    # Load similarity index for query and calculate the similary metric of the query article
    similarity_index = similarities.SparseMatrixSimilarity.load(
                        path+'lda_similarity_index_{0}_{1}_nobelow{2}_noabove{3}.pickle'.format(category, n_topics, no_below, no_above))                        
    similarity = similarity_index[doc_lda]
    sim_sorted = sorted(enumerate(similarity,start=1), key=lambda item: -item[1])
    
    
    if query_only:
        return sim_sorted, word_level
    else:
        # convert to data frame, sort the data frame according toprobability
        doc_lda=DataFrame(doc_lda, columns=['topicid','prob'])
        doc_lda.sort(columns='prob',ascending=False, inplace=True)
        # redo the index 
        doc_lda.index = arange(0,len(doc_lda))   
        
        return sim_sorted, word_level, lda_model, doc_lda, doc_trigram
        

