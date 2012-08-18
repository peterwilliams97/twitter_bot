from common import *

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

def _preprocess(words):
    """ !@#$ Stub"""
    return words

def get_cntv(counts):
    """counts is a dict of word:(p,n) where
            p is number of times word has appeared in a +ve
            n is number of times word has appeared in a -ve
        returns cntp,cntn,v
            cntp: number of p
            cntn: number of n
            v = number of entries in counts
    """    
    cntp = sum([p for p,n in counts.values()])
    cntn = sum([n for p,n in counts.values()])
    v = len(counts.keys())
    return cntp,cntn,v
    
class BayesClassifier:
    
    class Example:
        """Represents a document with a label. klass is 'pos' or 'neg' by convention.
            words is a list of strings.
        """
        def __init__(self):
            self.kls = UNKNOWN
            self.words = []

    def __init__(self):
        """BayesClassifier initialization"""
       
        self.unigram_counts = {}
        self.unigram_keys = set([]) 
        self.bigram_counts = {}
        self.bigram_keys = set([])
        self.trigram_counts = {}
        self.trigram_keys = set([])
        self.class_count = [0,0]

    def addExample(self, kls, words):
        """
         * Train your model on an example document with label klass ('pos' or 'neg') and
         * words, a list of strings.
         * You should store whatever data structures you use for your classifier 
         * in the NaiveBayes class.
         * Returns nothing
        """

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
                count[kls] += 1
                ngram_counts[k] = count
                ngram_keys.add(k)

        self.class_count[kls] += 1
        update_ngrams(unigrams, self.unigram_counts, self.unigram_keys)
        update_ngrams(bigrams,  self.bigram_counts,  self.bigram_keys)
        update_ngrams(trigrams, self.trigram_counts, self.trigram_keys)

    def train(self, tweets):
        for t in tweets:
            self.addExample(t[0], t[1].split())
            
        self.cntv_unigrams = get_cntv(self.unigram_counts)
        self.cntv_bigrams  = get_cntv(self.bigram_counts)   
        self.cntv_trigrams = get_cntv(self.trigram_counts)
        
        print '                  (pos, neg, cnt)'
        print 'self.cntv_unigrams', self.cntv_unigrams
        print ' self.cntv_bigrams', self.cntv_bigrams
        print 'self.cntv_trigrams', self.cntv_trigrams
        
    def __repr__(self):    
        def positivity(pn):
            return (pn[0] - pn[1])/(pn[0] + pn[1]) 
        def show(s, pn):
            return '%s %.1f "%s"' % (pn, positivity(pn), s)
        def counts_str(counts):
            print counts
            def p(k):  return positivity(counts[k])
            return '\n'.join([show(key, counts[key]) for key in sorted(counts, key = lambda k : -p(k))])
        def show_counts(name, counts):
            return '%s\n%s\n%s\n' % (name, counts_str(counts), '-' * 80)
        return show_counts('unigrams', self.unigram_counts) \
             + show_counts('bigrams', self.bigram_counts) \
             + show_counts('trigrams', self.trigram_counts) \

    def classify(self, words):
        """ 
            'words' is a list of words to classify. Return 'pos' or 'neg' classification.
        """
        words = _preprocess(words)
        unigrams = words
        bigrams = _get_bigrams(words)
        trigrams = _get_trigrams(words)

        # "Binarize"
        unigrams = set(unigrams)
        bigrams = set(bigrams)
        trigrams = set(trigrams)

        def get_score(counts, cntv, alpha):
            p,n = counts
            if p == n:
                return 0
            cntp,cntn,v  = cntv
            dp = cntp + v * alpha
            dn = cntn + v * alpha
            return math.log((p+alpha)/dp) - math.log((n+alpha)/dn) 

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
  

