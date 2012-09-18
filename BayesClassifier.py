from __future__ import division
"""
    Simple bag of n-grams classifier for tweets
    
    Classifies messages based on their bigrams. 
    If a trigram in message is not in model then backs off to bigrams.
    If a bigram in message is not in model then backs off to unigrams.

    Trigram, bigram and unigram likliehoods are all smooothed
    
    A tunable threshold is classifying based on posterior probabalities
    
    The paramaters for all these things are at the start of BayesClassifier
"""
import math
import preprocessing

def _cnt_positivity(np):
    """np is (n,p) where p is num positives and n
        is number of negatives
        Return how positive this result is
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
   
    # Precision = 0.947, Recall = 0.649, F1 = 0.770
    smooth_unigram = 11.4338
    smooth_bigram = 4.5718
    smooth_trigram = 0.5261
    backoff_bigram = 0.8718
    backoff_trigram = 0.4252
    threshold = 1.8402


    @staticmethod
    def make_valid(param):
        """This keeps values sane when running an optimizer on set_params()"""
        return max(param, 0.01)
    
    @staticmethod
    def set_params(smooth_unigram, smooth_bigram, smooth_trigram, 
        backoff_bigram, backoff_trigram, threshold):
        
        BayesClassifier.smooth_unigram = BayesClassifier.make_valid(smooth_unigram) 
        BayesClassifier.smooth_bigram = BayesClassifier.make_valid(smooth_bigram)   
        BayesClassifier.smooth_trigram = BayesClassifier.make_valid(smooth_trigram)  
        BayesClassifier.backoff_bigram = BayesClassifier.make_valid(backoff_bigram)
        BayesClassifier.backoff_trigram = BayesClassifier.make_valid(backoff_trigram)
        BayesClassifier.threshold = threshold

    @staticmethod    
    def get_params():
        return (
            BayesClassifier.smooth_unigram,
            BayesClassifier.smooth_bigram,    
            BayesClassifier.smooth_trigram,  
            BayesClassifier.backoff_bigram, 
            BayesClassifier.backoff_trigram,
            BayesClassifier.threshold
        )
    
    @staticmethod    
    def get_param_names(): 
        return (
            'smooth_unigram',
            'smooth_bigram',
            'smooth_trigram', 
            'backoff_bigram', 
            'backoff_trigram',
            'threshold'
        )

    @staticmethod
    def get_features(ngrams):
        """Make features to classify on from ngrams
        """    
        
        counts = {}
        for w in ngrams:
            counts[w] = counts.get(w,0) + 1
        features = []
        
        for k,v in counts.items():
            features.append(k)
            for cnt in range(2,min(3,v)+1): 
                features.append('%s (COUNT=%d)' % (k,cnt))

        return features        
    
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

        self.train(training_data)
        
    def __repr__(self):    

        def counts_str(counts):
            def n(k):  return -_cnt_positivity(counts[k]), k.lower()
            return '\n'.join([_cnt_show(key, counts[key]) for key in sorted(counts, key = lambda k : n(k))])

        def show_counts(name, counts):
            return '%s\n%s\n%s\n' % ('-' * 80, name, counts_str(counts))

        totals = [
            '          (neg,   pos,   cnt)',
            'TRIGRAMS %s' % str(self.cntv_trigrams),
            ' BIGRAMS %s' % str(self.cntv_bigrams),
            'UNIGRAMS %s' % str(self.cntv_unigrams),
        ]   
        totals_string = '\n'.join(totals) + '\n'
        
        return totals_string \
             + show_counts('TRIGRAMS', self.trigram_counts) \
             + show_counts('BIGRAMS', self.bigram_counts) \
             + show_counts('UNIGRAMS', self.unigram_counts) 
    

    def _add_example(self, cls, message):
        """Add a training example
        """
            
        words = preprocessing.extract_words(message)
        if not words:
            return
        unigrams = words[1:-1]
        bigrams = preprocessing.get_bigrams(words)
        trigrams = preprocessing.get_trigrams(words)
        
        unigrams = BayesClassifier.get_features(unigrams)
        bigrams = BayesClassifier.get_features(bigrams)
        trigrams = BayesClassifier.get_features(trigrams)

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

    def train(self, training_data):
        for cls,message in training_data:
            self._add_example(cls, message)

        self.cntv_unigrams = _get_cntv(self.unigram_counts)
        self.cntv_bigrams  = _get_cntv(self.bigram_counts)   
        self.cntv_trigrams = _get_cntv(self.trigram_counts)


    def classify(self, message, detailed=False):
        """message is a string to classify. Return True or False classification.
            
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
        words = preprocessing.extract_words(message)
        if detailed:
            print words
        if not words:
            return False, 0.0    
        
        # Using dicts with offset keys prevents the same ngram being included twice
        unigrams = {}
        bigrams = {}
        trigrams = {}
        
        from preprocessing import WORD_DELIMITER
        # Best intuition is to compute back-off based on counts
        for i in range(len(words)-3):
            tri = WORD_DELIMITER.join(words[i:i+3])
            if tri in self.trigram_keys:
                trigrams[i] = tri
            else:
                for j in (0,1):
                    bi = WORD_DELIMITER.join(words[i+j:i+j+2])
                    if bi in self.bigram_keys:
                        bigrams[i+j] = bi
                    else:
                        for k in (0,1):
                            unigrams[i+j+k] = words[i+j+k]
        
        unigrams = BayesClassifier.get_features(unigrams.values())
        bigrams = BayesClassifier.get_features(bigrams.values())
        trigrams = BayesClassifier.get_features(trigrams.values())        

        def get_score(counts, cntv, alpha):
            """Get a smoothed score for an ngram
                
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

        if detailed:
            def _dbg(n, score, k):
                spacer = '  ' * (3-n) 
                print '%d%s [%.2f] %s' % (n, spacer, score,k)
        else:
             def _dbg(n, score, k): pass
            
        def unigram_score(k):
            score = get_score(self.unigram_counts.get(k, [0,0]), self.cntv_unigrams, BayesClassifier.smooth_unigram)
            _dbg(1, score, k)
            return score
            
        def bigram_score(k):
            score = get_score(self.bigram_counts.get(k, [0,0]), self.cntv_bigrams, BayesClassifier.smooth_bigram)
            _dbg(2, score, k)
            return score

        def trigram_score(k):
            if detailed: print '-----', k
            score = get_score(self.trigram_counts.get(k, [0,0]), self.cntv_trigrams, BayesClassifier.smooth_trigram)
            _dbg(3, score, k)
            return score

        n,p = self.class_count
        prior = math.log(p) - math.log(n)    
        likelihood = sum(trigram_score(k) for k in trigrams) \
                   + BayesClassifier.backoff_trigram *(sum(bigram_score(k) for k in bigrams) 
                   + (BayesClassifier.backoff_bigram * sum(unigram_score(k) for k in unigrams))) 
        likelihood /= 1.0 + BayesClassifier.backoff_trigram + BayesClassifier.backoff_bigram          
        log_odds = prior + likelihood
        
        if detailed:
            n_gram_dict = {}
            for k in trigrams: n_gram_dict[k] = trigram_score(k) 
            for k in  bigrams: n_gram_dict[k] = bigram_score(k) * BayesClassifier.backoff_trigram
            for k in unigrams: n_gram_dict[k] = unigram_score(k) * BayesClassifier.backoff_trigram * BayesClassifier.backoff_bigram
            print 'ngrams scores --------------'
            for k in sorted(n_gram_dict, key = lambda x: n_gram_dict[x]):
                print '%6.3f : %s ' % (n_gram_dict[k], k)  

        return log_odds > BayesClassifier.threshold, log_odds

def test():
    """Run some tests on the code"""
   
    # Test _remove_quoted_text()
    def test_remove_quoted_text(test):
        print test
        #for m in RE_QUOTE.finditer(test):
        #    print m.start(), m.groups()
        print _remove_quoted_text(test) 
        print '-' * 80        
    tests = [
        '''I'm out of here ' right now' like "now!"''',
        '''I'm out of here 'right now' like "now!"''',
        '''"I just gave myself a paper cut" "Congratulations how do you feel?"''',
        ''' You really are living the life. ?@sockin_bxxches: just got a paper cut from counting money...no boost? ''',
        ''' life. ?@sockin_bxxches: just got a paper cut'''
    ]    
    print '=' * 80
    for test in tests:
        test_remove_quoted_text(test)  

    
    # Test _pre_tokenize()
    for message in ['PaperCut owwwww. #hash',
        '''You really are living the life. ?@sockin_bxxches: just got a paper cut from counting money...no boost?''']:    
        print message
        print _pre_tokenize(message)

        
if __name__ == '__main__':
    # Just dump the BayesClassifier class to stdout  
    for k in sorted(BayesClassifier.__dict__):
        if 'gram' in k:
            print '%20s : %s' % (k, BayesClassifier.__dict__[k])
    
