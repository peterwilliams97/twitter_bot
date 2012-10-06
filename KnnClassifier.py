# -*- coding: utf-8 -*-
from __future__ import division
"""
    A basic KNN classifier
    
    http://nlp.stanford.edu/IR-book/pdf/14vcat.pdf
    
    The basic idea here is to represent each document as a vector of counts 
    of ngrams.
    
        - The vectors are normalized to length 1
        - New documents are classifier according the K training documents 
           they are closest to.
        - In the current implementation, the distance measure is cosine.
    
    This does not seem to be well-suited to tweet classification as the
    vectors are all sparse with element values rarely greater than 1.
"""
import math, heapq
import preprocessing
from vectorizer_lib import TfidfVectorizer

class KnnClassifier:

    K = 20 
 
    # Precision = 0.716, Recall = 0.716, F1 = 0.716
    weight_bigrams = 4.4661
    weight_trigrams = 15.8206
    backoff = 0.9867
    backoff2 = 0.9895
    threshold = 0.4948
    
    @staticmethod
    def set_params(weight_bigrams, weight_trigrams, backoff, backoff2, threshold):
        KnnClassifier.weight_bigrams = weight_bigrams
        KnnClassifier.weight_trigrams = weight_trigrams   
        KnnClassifier.backoff = backoff  
        KnnClassifier.backoff2 = backoff2          
        KnnClassifier.threshold = threshold   

    @staticmethod    
    def get_params():
        return (
            KnnClassifier.weight_bigrams, 
            KnnClassifier.weight_trigrams,  
            KnnClassifier.backoff,
            KnnClassifier.backoff2,    
            KnnClassifier.threshold            
        )
    
    @staticmethod    
    def get_param_names(): 
        return (
            'weight_bigrams',
            'weight_trigrams',
            'backoff',
            'backoff2',    
            'threshold'  
        ) 
    
    @staticmethod
    def get_weights():
        weights = {
            1 : 1.0, 
            2 : KnnClassifier.weight_bigrams, 
            3 : KnnClassifier.weight_trigrams
        }
        total = sum(weights.values())
        return dict((n,w/total) for n,w in weights.items()) 

    
    def __init__(self, training_data):
        """KnnClassifier initialization

        """

        self.documents = dict((n,[]) for n in (1,2,3))
        self.vectorizers = {}
       
        self.train(training_data)
        
    def __repr__(self):
        
        def show_pos_neg(n, vocab, pos_centroid, neg_centroid):
            def pn(word):
                p = pos_centroid.get(word, 0.0)
                n = neg_centroid.get(word, 0.0)
                return '%6.4f - %6.4f = %7.4f %s' % (p, n, p-n, word)
            def order(word):
                return neg_centroid.get(word, 0.0) - pos_centroid.get(word, 0.0)
            return 'pos neg n=%d\n%s' % (n, '\n'.join(pn(word) for word in sorted(vocab, key = order)))
        
        return '\n'.join(show_pos_neg(n, self.vocab[n], self.pos_centroid[n], self.neg_centroid[n]) 
            for n in (3,2,1)) 

    def _add_example(self, cls, message):
        """Add a training example
        """

        words = preprocessing.extract_words(message)
        if not words:  # Treat cases where 'paper cut' is pre-processing as negatives. 
            return

        # Update self.documents[n] and self.vocab[n] for ngrams   and cls
        for n in (1,2,3):
            ngrams = preprocessing.get_ngrams(n, words)
            self.documents[n].append((cls,ngrams))

    def train(self, training_data):
        for cls,message in training_data:
            self._add_example(cls, message)
            
        for n in (1,2,3):
            self.vectorizers[n] = TfidfVectorizer([doc for _,doc in self.documents[n]])

    def classify(self, message, detailed=False):
        """ 
            'message' is a string to classify. Return True or False classification.
            
            Method is to calculate a log_odds from a liklihood based on
            trigram, bigram and unigram (p,n) counts in the training set
            For each trigram
                return smoothed trigram score if trigram in training set, else
                for the 2 bigrams in the trigram
                    return smoothed bigram score if bigram in training set, else
                    for the 2 unigrams in the bigram
                        return smoothed unigram score
                        
            get_score() shows the smoothed scoring    
            <n>gram_score() shows the backoff and smoothing factors    
        """

        def get_docs_with_terms(vectorizer, ngrams):
            docs = set()
            for term in ngrams:
                if term in vectorizer.vocab:
                    docs |= set(vectorizer.tfidf[term].keys())
            return docs
            
        def get_nearest(K, documents, vectorizer, ngrams, doc_ids):
            """Return doc ids of K documents nearest query_vec
            """
            # Compute scores and add to a priority queue
            scores = []
            for i in doc_ids:
                heapq.heappush(scores, (vectorizer.get_distance(i, ngrams), i, documents[i][0]))
            # Return top K scores
            return [(cls,i,dist) for dist,i,cls in heapq.nlargest(K,scores)]

        words = preprocessing.extract_words(message)
        if not words:
            return False, 0.0

        ngrams = dict((n,preprocessing.get_ngrams(n, words)) for n in (1,2,3))

        diffs = {}    
        for n in (1,2,3):
            doc_ids = get_docs_with_terms(self.vectorizers[n], ngrams[n])
            nearest = get_nearest(KnnClassifier.K, self.documents[n], self.vectorizers[n], ngrams[n], doc_ids )
                        
            pos = sum((1 if cls else -1) * (KnnClassifier.backoff ** k) for k,(cls,_,_) in enumerate(nearest))
            max_pos = sum(KnnClassifier.backoff ** k for k in range(len(nearest)))
            
            # pos2/max_pos2 is in range [-1,+1]
            pos2 = sum((1 if cls else -1) * (KnnClassifier.backoff2 ** (2*k)) for k,(cls,_,_) in enumerate(nearest))
            max_pos2 = sum(KnnClassifier.backoff2 ** (2*k) for k in range(len(nearest)))
   
            pos *= pos2
            max_pos *= max_pos2

            diffs[n] = pos/max_pos if max_pos else 0.0 
       
        weights = KnnClassifier.get_weights()   
        diff = sum(diffs[n]*weights[n] for n in (1,2,3))      

        return diff > KnnClassifier.threshold, diff

if __name__ == '__main__':
    # Just dump the KnnClassifier class to stdout  
    for k in sorted(KnnClassifier.__dict__):
        print '%20s : %s' % (k, BayesClassifier.__dict__[k])
    
