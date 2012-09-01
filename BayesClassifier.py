from __future__ import division
import math, re
from common import *

RE_QUOTE = re.compile(r'''(?:'(?!\S)|(?<!\S)'|")''')

# In Twitter 'some text @someone: some quote' is a way of quoting 'some quote'
# You really are living the life. ?@sockin_bxxches: just got a paper cut from counting money...no boost?
RE_QUOTE2 = re.compile(r'@\w+\s*:.+$')

def _remove_quoted_text(message):
    """Remove quoted text from message because it we presume it was 
        not written the author of message
        by some
    """
    
    message = RE_QUOTE2.sub(' ', message)
    
    # Split message by ' and "
    parts = RE_QUOTE.split(message)

    # in_quote is true between quote marks
    # discard these parts
    in_quote = False
    out_parts = []
    for p in parts:
        out_parts.append(' ' if in_quote else p)
        in_quote = not in_quote
  
    return ' '.join(out_parts)    

if False:   
   
    def do_test(test):
        print test
        #for m in RE_QUOTE.finditer(test):
        #    print m.start(), m.groups()
        print _remove_quoted_text(test) 
        print '-' * 80        
    test1 = '''I'm out of here ' right now' like "now!"'''
    test2 = '''I'm out of here 'right now' like "now!"'''
    test3 = '''"I just gave myself a paper cut" "Congratulations how do you feel?"'''
    test4 = ''' You really are living the life. ?@sockin_bxxches: just got a paper cut from counting money...no boost? '''
    
    print RE_QUOTE2.search(test4).group(0)
    print '=' * 80
    for test in (test1,test2,test4):
        do_test(test)
    exit()   


RE_USER = re.compile(r'@\w+')
RE_HTTP = re.compile(r'http://\S+')

RE_SYM = re.compile(r'&(\w+);')
RE_SYM2 = re.compile(r'(\[TAG_SYMBOL\])\1\1*')

RE_AMP = re.compile(r'&amp;')
RE_GT = re.compile(r'&gt;')
RE_LT = re.compile(r'&lt;')
RE_PUNC = re.compile(r'[,.;:-]')
RE_PUNC2 = re.compile(r'[!?\']{2,}')
RE_PUNC3 = re.compile(r'\?')
RE_PUNC4 = re.compile(r'\?[\s\?]+')
RE_SPACE = re.compile(r'\s+')
RE_HASH = re.compile(r'#(\w+)')
# Not sure why this is so effecitve f 0.821 -> 0.827
RE_REPEAT = re.compile(r'(.)\1\1*') # RE_REPEAT = re.compile(r'(.)\1\1+')
RE_BANG = re.compile(r'(\w+)([!])')
RE_NUMBER = re.compile(r'\d+(\s+\d)*')

RE_PAPERCUT = re.compile(r'\b#?paper\s*cuts?\b')
def _pre_process(message):
    
    if not RE_PAPERCUT.search(message):
        return '[TAG_BOGUS]'
    
    message = RE_USER.sub('[TAG_USER]', message)
    message = RE_HTTP.sub('[TAG_LINK]', message)
    
    #message = RE_AMP.sub(' & ', message)
    #message = RE_GT.sub(' < ', message)
    #message = RE_LT.sub(' > ', message)
    
    #message = RE_SYM.sub(r' \1 ', message) 
    message = RE_SYM.sub(r'[TAG_SYMBOL]', message) 
    message = RE_SYM2.sub(r'[TAG_SYMBOL]', message) 
    
    message = RE_PUNC.sub(' ', message)
    message = RE_PUNC2.sub('!', message)
    message = RE_PUNC3.sub(r' ? ', message)
    message = RE_PUNC4.sub(r' ? ', message)
    
    #print message
    message = RE_SPACE.sub(' ', message)
    #print message
    message = RE_HASH.sub(r'\1', message)
    #print message
    message = RE_REPEAT.sub(r'\1', message) # message = RE_REPEAT.sub(r'\1\1', message)
    message = RE_BANG.sub(r'\1 \2', message)
    
    message = RE_NUMBER.sub('[TAG_NUMBER]', message)
    
    #message = _remove_quoted_text(message)
    return message
    
STOP_WORDS = set([
    #'the',
    #'and', 
   # 'a',
   # 'in', 'on', 'at'
    ])    
    
if False:    
    message = 'PaperCut owwwww. #hash'
    print message
    print _pre_process(message)
    exit()

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
    
    # 0.825127334465 [ 4.664691    3.31914489  3.40044725  0.52437482  0.78608935]
    # 0.828851899274 [ 4.75384442  3.20345303  3.21919898  0.53177478  0.82933903]
    # 0.831708350996 [ 4.95464452  3.2800687   3.08317047  0.52991956  0.82849809]
    # 0.839783603829 [ 5.09983195  3.33672827  3.18971037  0.48990963  0.83392737]
    smooth_unigram = 5.010 #4.754 # 4.35  # 3.5
    smooth_bigram = 3.337 #3.203 # 3.5
    smooth_trigram = 3.190 #3.219 # 3.5 
    backoff_bigram = 0.490 # 0.532 # 0.489 # 0.1 
    backoff_trigram = 0.834 # 0.829 # 0.798 # 0.5

    @staticmethod
    def set_params(smooth_unigram, smooth_bigram, smooth_trigram, 
        backoff_bigram, backoff_trigram):
        
        BayesClassifier.smooth_unigram = smooth_unigram 
        BayesClassifier.smooth_bigram = smooth_bigram   
        BayesClassifier.smooth_trigram = smooth_trigram  
        BayesClassifier.backoff_bigram = backoff_bigram
        BayesClassifier.backoff_trigram = backoff_trigram
        
    # This should be a hook
    @staticmethod
    def pre_tokenize(message):
        message = _pre_process(message)
        return message

    @staticmethod
    def post_tokenize(words):
        """ !@#$ Stub"""
        #words = [w for w in words if w not in STOP_WORDS]
        return words   
        
    @staticmethod
    def extract_words(message):
        message = message.lower()
        message = BayesClassifier.pre_tokenize(message)
        words = message.split()
        return BayesClassifier.post_tokenize(words)    

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
            
        words = BayesClassifier.extract_words(message)
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
             + show_counts('unigrams', self.unigram_counts) 

   
    def classify(self, message, detailed=False):
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
        words = BayesClassifier.extract_words(message)
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
            if k not in self.bigram_keys:
                w1,w2 = _U(k) 
                return (unigram_score(w1) + unigram_score(w2)) * BayesClassifier.backoff_bigram 
            score = get_score(self.bigram_counts.get(k, [0,0]), self.cntv_bigrams, BayesClassifier.smooth_bigram)
            _dbg(2, score, k)
            return score

        def trigram_score(k):
            if detailed: print '-----', k
            if k not in self.trigram_keys:
                w1,w2,w3 = _U(k)
                return (bigram_score(_B(w1,w2)) + bigram_score(_B(w2,w3))) * BayesClassifier.backoff_trigram 
            score = get_score(self.trigram_counts.get(k, [0,0]), self.cntv_trigrams, BayesClassifier.backoff_trigram)
            _dbg(3, score, k)
            return score

        n,p = self.class_count
        prior = math.log(p) - math.log(n)    
        likelihood = sum([trigram_score(k) for k in trigrams])
        log_odds = prior + likelihood
        
        if detailed:
            return log_odds > 0.0, log_odds, dict((trigram_score(k),k) for k in trigrams) 
        else:
            return log_odds > 0.0, log_odds
  

