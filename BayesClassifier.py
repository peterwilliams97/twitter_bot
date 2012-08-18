from common import *

def _tokenize(message):
    return message.split()

def _preprocess(words):
    """ !@#$ Stub"""
    return words

def _U(ngram):
    return ngram.split(' ')

def _B(w1, w2):
    return '%s %s' % (w1, w2)

def _T(w1, w2, w3):
    return '%s %s %s' % (w1, w2, w3)   
    
def _exclude(words):
    return [w for w in words if w not in _EXCLUSIONS] 

def _get_bigrams(words):    
    return [_B(words[i-1],words[i]) for i in range(1,len(words))]

def _get_trigrams(words):    
    return [_T(words[i-2],words[i-1],words[i]) for i in range(2,len(words))]

def _cnt_positivity(pn):
    """pn is (p,n) where p is num positives and n
        is number of negatives
        return how positive this resultit
    """
    if pn[0] == 0 or pn[1] == 0:
        return pn[0] - pn[1]
    return (pn[0] - pn[1])/(pn[0] + pn[1]) 
            
def _cnt_show(ngram, pn):
    """Return a string for an ngram with pn = (p,n)
        positive and negative counts
    """    
    return "[%3d,%3d] %4.1f '%s'" % (pn[0], pn[1], _cnt_positivity(pn), ngram)    

def _get_cntv(counts):
    """counts is a dict of ngram:(p,n) where
            p is number of times ngram has appeared in a +ve
            n is number of times ngram has appeared in a -ve
        returns cntp,cntn,v
            cntp: total number of positives
            cntn: total number of negatives
               v: number of unique ngrams
    """    
    cntp = sum([p for p,n in counts.values()])
    cntn = sum([n for p,n in counts.values()])
    v = len(counts.keys())
    return cntp,cntn,v
    
class BayesClassifier:
    
    class Example:
        """Represents a document with a label. cls is True, False or UNKNOWW
            words is a list of strings.
        """
        def __init__(self):
            self.cls = UNKNOWN
            self.words = []

    def __init__(self):
        """BayesClassifier initialization
            <n>gram_counts are dicts of postive and negative
                counts for each <n>gram
            <n>gram_counts[k] = [p,n]
            
            <n>gram_keys is <n>gram_counts' key set
            
            class_count = [p,n] is the total counts of positve
                and negative examples
        """
       
        self.unigram_counts = {}
        self.unigram_keys = set([]) 
        self.bigram_counts = {}
        self.bigram_keys = set([])
        self.trigram_counts = {}
        self.trigram_keys = set([])
        self.class_count = [0,0]

    def _add_example(self, cls, message):
        """
            Add a training example
        """

        words = _tokenize(message)
        words = _preprocess(words)
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

        self.class_count[cls] += 1
        update_ngrams(unigrams, self.unigram_counts, self.unigram_keys)
        update_ngrams(bigrams,  self.bigram_counts,  self.bigram_keys)
        update_ngrams(trigrams, self.trigram_counts, self.trigram_keys)

    def train(self, tweets):
        for t in tweets:
            self._add_example(t[0], t[1])
            
        self.cntv_unigrams = _get_cntv(self.unigram_counts)
        self.cntv_bigrams  = _get_cntv(self.bigram_counts)   
        self.cntv_trigrams = _get_cntv(self.trigram_counts)
        
        print '                  (pos, neg, cnt)'
        print 'self.cntv_unigrams', self.cntv_unigrams
        print ' self.cntv_bigrams', self.cntv_bigrams
        print 'self.cntv_trigrams', self.cntv_trigrams
        
    def __repr__(self):    
        
        def counts_str(counts):
            def n(k):  return -_cnt_positivity(counts[k]), k.lower()
            return '\n'.join([_cnt_show(key, counts[key]) for key in sorted(counts, key = lambda k : n(k))])
            
        def show_counts(name, counts):
            return '%s\n%s\n%s\n' % (name, counts_str(counts), '-' * 80)
            
        return show_counts('unigrams', self.unigram_counts) \
             + show_counts('bigrams', self.bigram_counts) \
             + show_counts('trigrams', self.trigram_counts) \

    def classify(self, message):
        """ 
            'message' is a string to classify. Return True or False classification.
            
            Method is to calculate a posterior from a liklihood based on
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
        words = _tokenize(message)
        words = _preprocess(words)
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
                
                counts = (p,n) 
                    p = number of positives for ngram in training set
                    n = number of negatives for ngram in training set 
                cntv = (cntp,cntn,v) for an ngram training dict
                    cntp: total number of positives
                    cntn: total number of negatives
                    v: number of unique ngrams
                alpha: a smoothing factor.  
                
                Returns: a smoothed score for the ngram         
            """
            p,n = counts
            if p == n:
                return 0
            cntp,cntn,v  = cntv
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

        p,n = self.class_count
        prior = math.log(p) - math.log(n)    
        likelihood = sum([trigram_score(k) for k in trigrams])
        posterior = prior + likelihood
        return posterior > 0
  

