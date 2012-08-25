from __future__ import division
import math, re
from common import *

RE_USER = re.compile(r'@\w+')
RE_HTTP = re.compile(r'http://\S+')

# This should be a hook
#
def _pre_tokenize(message):
    message = RE_USER.sub('[TAG_USER]', message)
    message = RE_HTTP.sub('[TAG_LINK]', message)
    return message

def _post_tokenize(words):
    """ !@#$ Stub"""
    return words

def _extract_words(message):
    message = message.lower()
    message = _pre_tokenize(message)
    words = message.split()
    return _post_tokenize(words)

def _U(ngram):
    return ngram.split(' ')

def _B(w1, w2):
    return '%s %s' % (w1, w2)

def _T(w1, w2, w3):
    return '%s %s %s' % (w1, w2, w3)   

def _get_bigrams(words):    
    return [_B(words[i-1],words[i]) for i in range(1,len(words))]

def _get_trigrams(words):    
    return [_T(words[i-2],words[i-1],words[i]) for i in range(2,len(words))]

def _cnt_positivity(np):
    """np is (n.p) where p is num positives and n
        is number of negatives
        return how positive this resultit
    """
    n,p = np
    if n == 0 or p == 0:
        return p - n
    return (p - n)/(p + n) 
            
def _cnt_show(ngram, np):
    """Return a string for an ngram with np = (n,p)
        positive and negative counts
    """    
    return "[%3d,%3d] %4.1f '%s'" % (np[0], np[1], _cnt_positivity(np), ngram)    

def _get_cntv(counts):
    """counts is a dict of ngram:(n,p) where
            n is number of times ngram has appeared in a -ve
            p is number of times ngram has appeared in a +ve
        returns cntn,cntp,v
            cntn: total number of negatives
            cntp: total number of positives
               v: number of unique ngrams
    """    
    cntn = sum([n for n,p in counts.values()])
    cntp = sum([p for n,p in counts.values()])
    v = len(counts.keys())
    return cntn,cntp,v
    
class BayesClassifier:
    
    class Example:
        """Represents a document with a label. cls is True or False
            words is a list of strings.
        """
        def __init__(self):
            self.cls = UNKNOWN
            self.words = []

    def __init__(self, training_data):
        """BayesClassifier initialization
            *gram_counts are dicts of positive and negative
                counts for each <n>gram
            *gram_counts[k] = [n,p]
            
            *gram_keys is *gram_counts' key set
            
            class_count = [n,p] is the total counts of negative and
                positive examples
        """
        
        self.unigram_counts = {}
        self.unigram_keys = set([]) 
        self.bigram_counts = {}
        self.bigram_keys = set([])
        self.trigram_counts = {}
        self.trigram_keys = set([])
        self.class_count = [0,0]

        if training_data:
            self.train(training_data)

    def _add_example(self, cls, message):
        """
            Add a training example
        """

        assert cls in set([False, True]), 'invalid cls=%s' % cls
            
        words = _extract_words(message)
        unigrams = words
        bigrams = _get_bigrams(words)
        trigrams = _get_trigrams(words)
      
        # "Binarize"
        # 0 or 1 occurrences of ngram in document
        unigrams = set(unigrams)
        bigrams = set(bigrams)
        trigrams = set(trigrams)

        def update_ngrams(ngrams, ngram_counts, ngram_keys):
            """Update ngram_counts and ngram_keys for ngrams
                and kls
            """
            for k in ngrams:
                count = ngram_counts.get(k, [0,0])
                count[cls] += 1
                ngram_counts[k] = count
                ngram_keys.add(k)
                #if k == 'papercut':
                #    print cls, ngram_counts[k], ngrams

        self.class_count[cls] += 1
        update_ngrams(unigrams, self.unigram_counts, self.unigram_keys)
        update_ngrams(bigrams,  self.bigram_counts,  self.bigram_keys)
        update_ngrams(trigrams, self.trigram_counts, self.trigram_keys)

    def train(self, training_data):
        for cls,message in training_data:
            self._add_example(cls, message)

        self.cntv_unigrams = _get_cntv(self.unigram_counts)
        self.cntv_bigrams  = _get_cntv(self.bigram_counts)   
        self.cntv_trigrams = _get_cntv(self.trigram_counts)

    def __repr__(self):    

        def counts_str(counts):
            def n(k):  return -_cnt_positivity(counts[k]), k.lower()
            return '\n'.join([_cnt_show(key, counts[key]) for key in sorted(counts, key = lambda k : n(k))])
            
        def show_counts(name, counts):
            return '%s\n%s\n%s\n' % ('-' * 80, name, counts_str(counts))
        
        totals = [
            '        (neg, pos, cnt)'
            'unigrams %s' % str(self.cntv_unigrams),
            ' bigrams %s' % str(self.cntv_bigrams),
            'trigrams %s' % str(self.cntv_trigrams),
        ]   
        totals_string = '\n'.join(totals) + '\n'
        
        return totals_string \
             + show_counts('trigrams', self.trigram_counts) \
             + show_counts('bigrams', self.bigram_counts) \
             + show_counts('unigrams', self.unigram_counts) \

    def classify(self, message):
        """ 
            'message' is a string to classify. Return True or False classification.
            
            Method is to calculate a log_odds from a liklihood based on
            trigram, bigram and unigram p,n counts in the training set
            For each trigram
                return smoothed trigram score if trigram in training set, else
                for the 2 bigrams in the trigram
                    return smoothed bigram score if bigram in training set, else
                    for the 2 unigrams in the bigram
                        return smoothed unigram score
                        
            get_score() shows the smoothed scoring    
            <n>gram_score() shows the backoff and smoothing factors    
        """
        words = _extract_words(message)
        unigrams = words
        bigrams = _get_bigrams(words)
        trigrams = _get_trigrams(words)

        # "Binarize"
        unigrams = set(unigrams)
        bigrams = set(bigrams)
        trigrams = set(trigrams)

        def get_score(counts, cntv, alpha):
            """
                Get a smoothed score for an ngram
                
                counts = (n,p) 
                    n = number of negatives for ngram in training set                    
                    p = number of positives for ngram in training set
                   
                cntv = (cntn,cntp,v) for an ngram training dict
                    cntn: total number of negatives
                    cntp: total number of positives
                    v: number of unique ngrams
                alpha: smoothing factor.  
                
                Returns: a smoothed score for the ngram         
            """
            n,p = counts
            if p == n:
                return 0
            cntn,cntp,v  = cntv
            return math.log((p+alpha)/(cntp+v*alpha)) - math.log((n+alpha)/(cntn+v*alpha)) 

        def unigram_score(k):
            return get_score(self.unigram_counts.get(k, [0,0]), self.cntv_unigrams, 3.5)
            
        def bigram_score(k):
            if k not in self.bigram_keys:
                w1,w2 = _U(k) 
                return (unigram_score(w1) + unigram_score(w2)) * 0.1 
            return get_score(self.bigram_counts.get(k, [0,0]), self.cntv_bigrams, 3.5)

        def trigram_score(k):
            if k not in self.trigram_keys:
                w1,w2,w3 = _U(k)
                return (bigram_score(_B(w1,w2)) + bigram_score(_B(w2,w3))) * 0.5 
            return get_score(self.trigram_counts.get(k, [0,0]), self.cntv_trigrams, 3.5)

        n,p = self.class_count
        prior = math.log(p) - math.log(n)    
        likelihood = sum([trigram_score(k) for k in trigrams])
        log_odds = prior + likelihood
        return log_odds > 0.0, log_odds 
  

