from __future__ import division
import twitter, os, time, sys, re, pickle, random
from common import *
from BayesClassifier import BayesClassifier

UNKNOWN = -1    
CLASS_STRINGS = {
    False: 'n',
    True: 'y',  
    UNKNOWN: '?'
}
STRING_CLASSES = dict([(v,k) for k,v in CLASS_STRINGS.items()])

def get_class(s):
    return STRING_CLASSES.get(s, UNKNOWN)
    
def get_labelled_tweets():    
    tweets = []
    fp = open(CLASS_FILE, 'rt')
    for i,ln in enumerate(fp):
        parts = [pt.strip() for pt in ln.split('|')]
        cls, message= get_class(parts[0]), parts[1]
        if cls in set([False,True]):
            tweets.append((cls, message))
    fp.close()
    return tweets

def get_classifier_for_labelled_tweets():
    return BayesClassifier(get_labelled_tweets())
    
def validate_basic(tweets): 
    assert tweets
    model = BayesClassifier(tweets)
    
    file(NGRAM_FILE, 'wt').write(str(model))

    ratings = [(model.classify(t[1]), t) for t in tweets]
    ratings.sort()
    ratings.reverse()

    fp = open(VALIDATION_FILE, 'wt')
    for r in ratings:
        fp.write('%s\n' % str(r))
    fp.close()  

def make_score():
    return dict([((a,p),0) for p in (False,True) for a in (False,True)])

def get_test_score(training_tweets, test_tweets, test_indexes):
    model = BayesClassifier(training_tweets)

    score = make_score()
    fp = []
    fn = []
    for i,t in enumerate(test_tweets):
        a = t[0]
        p, log_odds = model.classify(t[1])
        score[(a,p)] += 1
        if p != a:
            if p: fp.append((test_indexes[i], log_odds))
            else: fn.append((test_indexes[i], log_odds))
    return score, fp, fn

def cross_validate(tweets, num_folds):
    confusion_matrix = make_score()
    false_positives = []
    false_negatives = []
    boundaries = [int(i*len(tweets)/num_folds) for i in range(num_folds + 1)]
    for i in range(1, len(boundaries)):
        begin,end = boundaries[i-1],boundaries[i]
        test_tweets = tweets[begin:end]
        training_tweets = tweets[:begin] + tweets[end:]
        score,fp,fn = get_test_score(training_tweets, test_tweets, range(begin,end))
        for k in score.keys():
            confusion_matrix[k] += score[k]
        false_positives += fp   
        false_negatives += fn  
    false_positives.sort()
    false_negatives.sort()
    return confusion_matrix, false_positives, false_negatives
  
def get_f(matrix):
    precision = matrix[(True,True)]/(matrix[(True,True)] + matrix[(False,True)])
    recall = matrix[(True,True)]/(matrix[(True,True)] + matrix[(True, False)])
    return 2.0/(1.0/precision + 1.0/recall)

def get_design(vals):
    """Return design matrix for which each element has all values
        in corresponding element of vals
    """
    
    def fill_design(design, row):
        if len(row) == len(vals):
            design.append(row)
        else:
            for v in vals[len(row)]:
                fill_design(design, row + [v])    

    design = []
    row = []
    fill_design(design, row)
    
    print '-' * 80
    print vals
    print '-' * 80
    for i,row in enumerate(design):
        print '%3d : %s' % (i, row)
    print '-' * 80
    
    return design
    
def optimize_params(tweets):
    from scipy import optimize
    
    def func(x):
        BayesClassifier.set_params(*x)
        f = -get_f(cross_validate(tweets, 10)[0])
        print -f, x
        return f
    
    smooth_unigram = 4.35  # 3.5
    smooth_bigram = 3.5
    smooth_trigram = 3.5 
    backoff_bigram = 0.489 # 0.1 
    backoff_trigram = 0.798 # 0.5
    x0 = [
        smooth_unigram,
        smooth_bigram,
        smooth_trigram, 
        backoff_bigram, 
        backoff_trigram
    ]
    x = optimize.fmin(func, x0)
    print '^' * 80
    print -func(x0), x0
    print -func(x), x
 
def print_confusion_matrix(confusion_matrix):  
    BAR = '-' * 5
    BAR2 = '=' * 5
    def print_matrix(matrix):
        print '%5s = %5s = %5s' % (BAR2, BAR2, BAR2) 
        print '%5s | %5s | %5s' % ('', False, True)
        print '%5s + %5s + %5s' % (BAR, BAR, BAR)  
        print '%5s | %5s | %5s' % (False, matrix[(False,False)], matrix[(False,True)]) 
        print '%5s + %5s + %5s' % (BAR, BAR, BAR)  
        print '%5s | %5s | %5s' % (True,  matrix[(True,False)],  matrix[(True,True)]) 
        print '%5s = %5s = %5s' % (BAR2, BAR2, BAR2)  
    
    total = sum([confusion_matrix[a,p] for p in (False,True) for a in (False,True)])

    percentage_matrix = {}
    for p in (False,True):
        for a in (False,True):
            percentage_matrix[p,a] = '%2d%%' % int(confusion_matrix[a,p]/total * 100.0)
            
    print_matrix(confusion_matrix)  
    print 'Total = %d' % total   
    print
    print_matrix(percentage_matrix) 
    print 'F2 = %.3f' % get_f(confusion_matrix)    
    print

def validate_full(tweets, show_errors, show_confusion, detailed):
    
    confusion_matrix,false_positives,false_negatives = cross_validate(tweets, 10)

    #print [i for i,p,g in false_positives]
    #print [i for i,p,g in false_negatives]

    if show_errors:
        print '-' * 80
        print 'FALSE NEGATIVES: %d' % len(set([(i,p) for i,p in false_negatives]))
        for i,p in sorted(set([(i,p) for i,p in false_negatives]), key = lambda x: x[1]):
            print '%5d %6.2f: %s' % (i,p, tweets[i][1]) 
            
        print '-' * 80
        print 'FALSE POSITIVES: %d' % len(set([(i,p) for i,p in false_positives]))
        for i,p in sorted(set([(i,p) for i,p in false_positives]), key = lambda x: x[1]):
            print '%5d %6.2f: %s' % (i,p, tweets[i][1])

    if show_confusion:
        print '-' * 80
        print_confusion_matrix(confusion_matrix)

    if detailed:  
        print '-' * 80
        POSTERIOR_LIMIT = 2.0  
          
        print '-' * 80
        print 'FALSE POSITIVE OUTLIERS'
        for i,p,g in sorted(false_positives, key = lambda x: x[1]):
            if abs(p) > POSTERIOR_LIMIT:
                print '%5d %6.2f: %s' % (i,p, tweets[i][1])
                for k in sorted(g, key = lambda x: g[x]):
                    print '%12.2f %s' % (g[k], k)
 
        print '-' * 80
        print 'FALSE NEGATIVE OUTLIERS'
        for i,p,g in sorted(false_negatives, key = lambda x: x[1]):
            if abs(p) > POSTERIOR_LIMIT:
                print '%5d %6.2f: %s' % (i,p, tweets[i][1])
                for k in sorted(g, key = lambda x: g[x]):
                    print '%12.2f %s' % (g[k], k)

def save_model(tweets):
    model = BayesClassifier(tweets)
    pickle.dump(model, open(MODEL_FILE, 'wb'))

def load_model():
    model = pickle.load(open(MODEL_FILE, 'rb'))
    return model

if __name__ == '__main__':

    import optparse

    parser = optparse.OptionParser('python ' + sys.argv[0] + ' [options] <text pattern> [<file pattern>]')
    parser.add_option('-o', '--optimize', action='store_true', dest='optimize', default=False, help='find optimum back-offs and smoothings')
    parser.add_option('-v', '--validate', action='store_true', dest='validate', default=False, help='do basic validation')
    parser.add_option('-f', '--full-validate', action='store_true', dest='summary_stats', default=False, help='full cross-validation')
    parser.add_option('-e', '--false-pos-neg', action='store_true', dest='false_pos_neg', default=False, help='show false positives and false negatives')
    parser.add_option('-m', '--model', action='store_true', dest='model', default=False, help='save calibration model')
    parser.add_option('-t', '--test-string', dest='test_string', default='', help='show ngrams for string')
    (options, args) = parser.parse_args()
    
    tweets = get_labelled_tweets() 
   
    if options.optimize:
        optimize_params(tweets)
        
    do_validate_full = options.summary_stats or options.false_pos_neg
    
    if options.validate or do_validate_full:
        validate_basic(tweets)
        
    if do_validate_full:
        print '=' * 80
        validate_full(tweets, options.false_pos_neg, options.summary_stats, False)
        
    if options.test_string:
        print options.test_string
        test = [t for t in tweets if options.test_string in t[1]]
        train =  [t for t in tweets if options.test_string not in t[1]]
        print test
        model = BayesClassifier(train)
        for cls, message in test:
            kls, log_odds, ngrams = model.classify(message, True)
            print kls, cls, log_odds
            for k in sorted(ngrams):
                print '%6.3f : %s ' % (k, ngrams[k])

    if options.model:
        save_model(tweets)

        