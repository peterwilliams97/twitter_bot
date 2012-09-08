from __future__ import division
"""
    Simple bag of n-grams classifier for tweets
    
    Classifies messages based on their bigrams. 
    If a trigram in message is not in model then backs off to bigrams.
    If a bigram in message is not in model then backs off to unigrams.

    Trigram, bigram and unigram likliehoods are all smooothed
    
    A tunable threshold is classifying based on posterior probabalities
    
    The paramates for all these things are at the start of BayesClassifier
    
   
"""
import math, re

RE_QUOTE = re.compile(r'''(?:'(?!\S)|(?<!\S)'|")''')

# In Twitter 'some text @someone: some quote' is a way of quoting 'some quote'
# You really are living the life. ?@sockin_bxxches: just got a paper cut from counting money...no boost?
RE_QUOTE2 = re.compile(r'@\w+\s*:.+$')
RE_QUOTE3 = re.compile(r'\brt\b.+$')

def _remove_quoted_text(message):
    """Remove quoted text from message because it we presume it was 
        not written the author of message
        by some
    """

    if True:
        message = RE_QUOTE2.sub(' ', message)

    if True:
        message = RE_QUOTE3.sub(' ', message)    
    
    if True:
        # Split message by ' and "
        parts = RE_QUOTE.split(message)

        # in_quote is true between quote marks
        # discard these parts
        in_quote = False
        out_parts = []
        for p in parts:
            out_parts.append(' ' if in_quote else p)
            in_quote = not in_quote
        message = ' '.join(out_parts) 
    return message    

if False:   
   
    def do_test(test):
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
#RE_PAPERCUT = re.compile(r'(?<!\S)#?paper[\s]*cuts?(?!\S)', re.IGNORECASE)
#RE_PAPERCUT2 = re.compile(r'(?<!\S)#?paper\s*cuts?(?!\S)', re.IGNORECASE)

def _pre_tokenize(message):

    if not RE_PAPERCUT.search(message):
        return '[TAG_BOGUS]'
    
    message = _remove_quoted_text(message)
    
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
    message = RE_SPACE.sub(' ', message)
    message = RE_HASH.sub(r'\1', message)
    message = RE_REPEAT.sub(r'\1', message) # message = RE_REPEAT.sub(r'\1\1', message)
    message = RE_BANG.sub(r'\1 \2', message)
  
    message = RE_NUMBER.sub('[TAG_NUMBER]', message)
     
    return message
  
if False:  
    message = '''You really are living the life. ?@sockin_bxxches: just got a paper cut from counting money...no boost?'''    
    print message
    print _pre_tokenize(message)
    exit()
    
STOP_WORDS = set([
    'the',
    'and',
    #'got',
    #'a',
    #'of'
   # 'in', 'on', 'at'
    ])    
    
if False:    
    message = 'PaperCut owwwww. #hash'
    print message
    print _pre_tokenize(message)
    exit()
    
def _post_tokenize(words):
    """Post-process list of words created from tokenization
        Remove stop words
        Remove words after indicators that they are not meants
    """
    words = [w for w in words if w not in STOP_WORDS]
    
    out_words = []
    skip_from = -1
    for i,w in enumerate(words):
        if skip_from >= 0:
            if i <= skip_from + 2:
                continue
            else:
                skip_from = -1
        if w in set(['almost']):
            skip_from = i
            continue
        out_words.append(w)    
    
    out_words = ['[TAG_START]'] + out_words +  ['[TAG_END]'] 
    return out_words      

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

    if False: # The values tried in the past
        # Precision = 0.957, Recall = 0.668, F1 = 0.787
        smooth_unigram = 6.2510
        smooth_bigram = 1.2650
        smooth_trigram = 1.1530
        backoff_bigram = 1.2490
        backoff_trigram = 0.1730
        threshold = 3.8590
        
        # Precision = 0.883, Recall = 0.848, F1 = 0.865
        smooth_unigram = 7.1519
        smooth_bigram = 1.3351
        smooth_trigram = 1.1283
        backoff_bigram = 1.3406
        backoff_trigram = 0.2189
        threshold = 1.2989
        
        # Precision = 0.956, Recall = 0.673, F1 = 0.790
        smooth_unigram = 8.8799
        smooth_bigram = 1.4472
        smooth_trigram = 1.0871
        backoff_bigram = 1.6691
        backoff_trigram = 0.2452
        threshold = 4.0944
    
    # Precision = 0.937, Recall = 0.741, F1 = 0.827
    smooth_unigram = 8.4423
    smooth_bigram = 4.4690
    smooth_trigram = 0.5298
    backoff_bigram = 0.7356
    backoff_trigram = 0.3505
    threshold = 3.7898

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
    def pre_tokenize(message):
        return _pre_tokenize(message)

    @staticmethod
    def post_tokenize(words):
        return _post_tokenize(words)
        
    @staticmethod
    def extract_words(message):
        """The word extractor that is run over every message that is trained on or
            classified
        """
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
        if detailed:
            print words
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
            if k not in self.trigram_keys:http://aws.amazon.com/python/
                w1,w2,w3 = _U(k)
                return (bigram_score(_B(w1,w2)) + bigram_score(_B(w2,w3))) * BayesClassifier.backoff_trigram 
            score = get_score(self.trigram_counts.get(k, [0,0]), self.cntv_trigrams, BayesClassifier.smooth_trigram)
            _dbg(3, score, k)
            return score

        n,p = self.class_count
        prior = math.log(p) - math.log(n)    
        likelihood = sum([trigram_score(k) for k in trigrams])
        log_odds = prior + likelihood
        
        if detailed:
            return log_odds > BayesClassifier.threshold, log_odds, dict((trigram_score(k),k) for k in trigrams) 
        else:
            return log_odds > BayesClassifier.threshold, log_odds
  
# Just dump the BayesClassifier class   
if __name__ == '__main__':
    for k in sorted(BayesClassifier.__dict__):
        print '%20s : %s' % (k, BayesClassifier.__dict__[k])
    
