# -*- coding: utf-8 -*-
from __future__ import division
"""
    Simple bag of ngrams classifier for tweets
    
    Classifies messages based on their trigrams. 
    If a trigram in message is not in model then backs off to bigrams.
    If a bigram in message is not in model then backs off to unigrams.

    Trigram, bigram and unigram likliehoods are all smooothed
    
    A tunable threshold is classifying based on posterior probabalities
    
    The paramaters for all these things are at the start of BayesClassifier
"""
import math
import preprocessing

class BayesClassifier:
   
    # Precision = 0.946, Recall = 0.685, F1 = 0.794
    smooth_unigram = 12.9621
    smooth_bigram = 4.5806
    smooth_trigram = 0.5088
    backoff_bigram = 0.8687
    backoff_trigram = 0.4266
    threshold = 1.7553
    
    @staticmethod
    def set_params(smooth_unigram, smooth_bigram, smooth_trigram, 
        backoff_bigram, backoff_trigram, threshold):
        
        BayesClassifier.smooth_unigram = smooth_unigram 
        BayesClassifier.smooth_bigram = smooth_bigram   
        BayesClassifier.smooth_trigram = smooth_trigram  
        BayesClassifier.backoff_bigram = backoff_bigram
        BayesClassifier.backoff_trigram = backoff_trigram
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
    def get_weights():
        weights = {
            1 : BayesClassifier.backoff_bigram,
            2 : BayesClassifier.backoff_trigram, 
            3 : 1.0 
        }
        total = sum(weights.values())
        return dict((n,w/total) for n,w in weights.items())  

    @staticmethod
    def get_smoothings():
        return { 
            1: BayesClassifier.smooth_unigram,
            2:  BayesClassifier.smooth_bigram,    
            3:  BayesClassifier.smooth_trigram
        }        
        
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
        
    @staticmethod    
    def get_cntv(counts):
        """counts is a dict of ngram:(neg,pos) where
                neg is number of times ngram has appeared in a -ve
                pos is number of times ngram has appeared in a +ve
            returns cntn,cntp,v
                cntn: total number of negatives
                cntp: total number of positives
                   v: number of unique ngrams
        """    
        cntn = sum([neg for neg,pos in counts.values()])
        cntp = sum([pos for neg,pos in counts.values()])
        v = len(counts.keys())
        return cntn,cntp,v 

    @staticmethod    
    def cnt_positivity(np):
        """np is (neg,pos) where pos is num positives and neg
            is number of negatives
            Return how positive this result is
        """
        neg,pos = np
        if neg == 0 or pos == 0:
            return pos - neg
        return (pos - neg)/(pos + neg) 

    @staticmethod
    def cnt_show(ngram, np):
        """Return a string for an ngram with np = neg,pos
            positive and negative counts
        """    
        return "[%3d,%3d] %4.1f '%s'" % (np[0], np[1], BayesClassifier.cnt_positivity(np), ngram)        
    
    def __init__(self, training_data):
        """BayesClassifier initialization
            ngram_counts are dicts of positive and negative
                counts for each ngrams for n = 1,2,3
            ngram_counts[n][term] = [neg,pos]
            
            ngram_keys[n] is ngram_counts[n]'s key set
            
            class_count = [neg,pos] is the total counts of negative and
                positive training examples
        """

        self.class_count = [0,0]
        self.ngram_counts = dict((n,{}) for n in (1,2,3))
        self.ngram_keys = dict((n,set()) for n in (1,2,3)) 
        
        self.train(training_data)
        
    def __repr__(self):    

        def counts_str(counts):
            def n(g):  return -BayesClassifier.cnt_positivity(counts[g]), g.lower()
            return '\n'.join([BayesClassifier.cnt_show(key, counts[key]) for key in sorted(counts, key = lambda k : n(k))])

        def show_counts(name, counts):
            return '%s\n%s\n%s\n' % ('-' * 80, name, counts_str(counts))

        totals = [
            '          (neg,   pos,   cnt)',
            'TRIGRAMS %s' % str(self.cntv_ngrams[3]),
            ' BIGRAMS %s' % str(self.cntv_ngrams[2]),
            'UNIGRAMS %s' % str(self.cntv_ngrams[1]),
        ]   
        totals_string = '\n'.join(totals) + '\n'
        
        return totals_string \
             + show_counts('TRIGRAMS', self.ngram_counts[3]) \
             + show_counts('BIGRAMS', self.ngram_counts[2]) \
             + show_counts('UNIGRAMS', self.ngram_counts[1]) 
    
    def _add_example(self, cls, message):
        """Add a training example
        """
        
        words = preprocessing.extract_words(message)
        if not words:  # Treat cases where 'paper cut' is pre-processing as negatives. 
            return
        
        self.class_count[cls] += 1        
        
        # Update ngram_counts and ngram_keys for ngrams cls
        for n in (1,2,3):
            ngrams = preprocessing.get_ngrams(n, words)
            ngrams = BayesClassifier.get_features(ngrams)  
            for g in ngrams:
                count = self.ngram_counts[n].get(g, [0,0])
                count[cls] += 1
                self.ngram_counts[n][g] = count
                self.ngram_keys[n].add(g)    
       
    def train(self, training_data):
        for cls,message in training_data:
            self._add_example(cls, message)

        self.cntv_ngrams = dict((n,BayesClassifier.get_cntv(self.ngram_counts[n])) for n in (1,2,3))

    def classify(self, message, detailed=False):
        """message is a string to classify. Return True or False classification.
            
            Method is to calculate a log_odds from a liklihood based on
            trigram, bigram and unigram (pos,neg) counts in the training set
            For each trigram
                return smoothed trigram score if trigram in training set, else
                for the 2 bigrams in the trigram
                    return smoothed bigram score if bigram in training set, else
                    for the 2 unigrams in the bigram
                        return smoothed unigram score
                        
            get_score() shows the smoothed scoring    
            gram_score() shows the backoff and smoothing factors    
        """
        words = preprocessing.extract_words(message)
        if detailed:
            print words
        if not words:
            return False, 0.0    
        
        # Using dicts with offset keys prevents the same ngram being included twice
        ngrams = dict((n,{}) for n in (1,2,3))
          
        from preprocessing import WORD_DELIMITER
        # Best intuition is to compute back-off based on counts
        for i in range(len(words)-3):
            tri = WORD_DELIMITER.join(words[i:i+3])
            if tri in self.ngram_keys[3]:
                ngrams[3][i] = tri
            else:
                for j in (0,1):
                    bi = WORD_DELIMITER.join(words[i+j:i+j+2])
                    if bi in self.ngram_keys[2]:
                        ngrams[2][i+j] = bi
                    else:
                        for k in (0,1):
                            ngrams[1][i+j+k] = words[i+j+k]
        
        for n in (1,2,3):
            ngrams[n] = BayesClassifier.get_features(ngrams[n].values())

        def get_score(counts, cntv, alpha):
            """Get a smoothed score for an ngram
                
                counts = neg,pos 
                    neg = number of negatives for ngram in training set                    
                    pos = number of positives for ngram in training set
                   
                cntv = (cntn,cntp,v) for an ngram training dict
                    cntn: total number of negatives
                    cntp: total number of positives
                    v: number of unique ngrams
                alpha: smoothing factor.  
                
                Returns: a smoothed score for the ngram         
            """
            neg,pos = counts
            if neg == pos:
                return 0
            cntn,cntp,v  = cntv
            return math.log((pos+alpha)/(cntp+v*alpha)) - math.log((neg+alpha)/(cntn+v*alpha)) 

        if detailed:
            def _dbg(n, score, g): print '%d%s [%.2f] %s' % (n, '  ' * (3-n), score, g)
        else:
            def _dbg(n, score, g): pass
 
        weights = BayesClassifier.get_weights()
        smoothings = BayesClassifier.get_smoothings()    
        
        def ngram_score(n, g):
            score = get_score(self.ngram_counts[n].get(g, [0,0]), self.cntv_ngrams[n], smoothings[n])
            _dbg(n, score, g)
            return score
        
        neg,pos = self.class_count
        
        prior = math.log(pos) - math.log(neg)   
        likelihood = sum(weights[n] * sum(ngram_score(n,g) for g in ngrams[n]) for n in (1,2,3))    
        log_odds = prior + likelihood
        
        if detailed:
            n_gram_dict = {}
            for n in (1,2,3):
                for g in ngrams[n]: 
                    n_gram_dict[g] = ngram_score(n,g) * weights[n] 
            print 'ngrams scores --------------'
            for k in sorted(n_gram_dict, key = lambda x: n_gram_dict[x]):
                print '%6.3f : %s ' % (n_gram_dict[k], k)  

        return log_odds > BayesClassifier.threshold, log_odds
       
if __name__ == '__main__':
    # Just dump the BayesClassifier class to stdout  
    for k in sorted(BayesClassifier.__dict__):
        if 'gram' in k:
            print '%20s : %s' % (k, BayesClassifier.__dict__[k])
    
