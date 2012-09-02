from __future__ import division
"""
    Peform various statistical tests on the labelled tweets in CLASS_FILE

""" 
import sys, re, random

# Our shared modules
from BayesClassifier import BayesClassifier
import common, definitions

def get_labelled_tweets():  
    """Load the labelled tweets we analyze from common.CLASS_FILE"""
    tweets = []
    fp = open(common.CLASS_FILE, 'rt')
    for i,ln in enumerate(fp):
        parts = [pt.strip() for pt in ln.split('|')]
        cls, message = definitions.get_class(parts[0]), parts[1]
        if cls in set([False,True]):
            tweets.append((cls, message))
    fp.close()
    return tweets
    
def show_ngrams(tweets): 
    """Print all the ngrams that the BayesClassifier saves for 
        a list of tweets
    """
    print BayesClassifier(tweets)

def show_self_validation(tweets):
    """Create a classification model based on tweets
        then classify all the entries in tweets with
        that model and print the results to stdout.
    """
    model = BayesClassifier(tweets)
    
    ratings = [(model.classify(t[1]), t) for t in tweets]
    ratings.sort()
    ratings.reverse()
    
    for (pred,log_lik),(actual,message) in ratings:
        print '%5.2f %5s %5s "%s"' % (log_lik, pred, actual, message)

#
# confusion_matrix[(a,p)] is count of actual==a, predicted==p 
#   
def get_empty_score():
    return dict([((a,p),0) for p in (False,True) for a in (False,True)])

def get_test_score(training_tweets, test_tweets, test_indexes):
    model = BayesClassifier(training_tweets)

    score = get_empty_score()
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
    confusion_matrix = get_empty_score()
    false_positives = []
    false_negatives = []
    boundaries = [int(i*len(tweets)/num_folds) for i in range(num_folds + 1)]
    for i in range(1, len(boundaries)):
        begin,end = boundaries[i-1],boundaries[i]
        test_tweets = tweets[begin:end]
        training_tweets = tweets[:begin] + tweets[end:]
        score,fp,fn = get_test_score(training_tweets, test_tweets, range(begin,end))
        assert score[(False,True)] == len(fp)
        assert score[(True,False)] == len(fn)
        for k in score.keys():
            confusion_matrix[k] += score[k]
        false_positives += fp   
        false_negatives += fn  
    false_positives.sort()
    false_negatives.sort()
    assert confusion_matrix[(False,True)] == len(false_positives)
    assert confusion_matrix[(True,False)] == len(false_negatives)
    return confusion_matrix, false_positives, false_negatives
  
def get_precision(matrix):
    return matrix[(True,True)]/(matrix[(True,True)] + matrix[(False,True)])

def get_recall(matrix):
    return matrix[(True,True)]/(matrix[(True,True)] + matrix[(True, False)])  
    
def get_f(matrix):
    return 2.0/(1.0/get_precision(matrix) + 1.0/get_recall(matrix))
    
def get_f_safe(matrix):
    return 4.0/(3.0/get_precision(matrix) + 1.0/get_recall(matrix))    

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
        #f = -get_f(cross_validate(tweets, 10)[0])
        f = -get_f_safe(cross_validate(tweets, 10)[0])
        print ' ', -f, x
        return f
  
    x0 = [
        smooth_unigram,
        smooth_bigram,
        smooth_trigram, 
        backoff_bigram, 
        backoff_trigram,
        threshold
    ]
    x = optimize.fmin(func, x0)
    print '^' * 80
    print -func(x0), x0
    print -func(x), list(x)
    
    PARAMS = ''' 
        BayesClassifier.smooth_unigram
        BayesClassifier.smooth_bigram
        BayesClassifier.smooth_trigram 
        BayesClassifier.backoff_bigram 
        BayesClassifier.backoff_trigram
        BayesClassifier.threshold
    '''
    param_names = [s.strip(' \n') for s in PARAMS.split('\n') if s.strip(' \n')]
    for k,v in zip(param_names, x):
        print '    %s = %.4f' % (k,v)
 
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
            percentage_matrix[a,p] = '%2d%%' % int(confusion_matrix[a,p]/total * 100.0)
            
    print_matrix(confusion_matrix)  
    print 'Total = %d' % total   
    print
    print_matrix(percentage_matrix) 
    print 'Precision = %.3f, Recall = %.3f, F2 = %.3f' % (
        get_precision(confusion_matrix), get_recall(confusion_matrix), get_f(confusion_matrix))    
    print

def show_cross_validation(tweets, show_errors):
    
    confusion_matrix,false_positives,false_negatives = cross_validate(tweets, 10)

    if show_errors:
        print '-' * 80
        print 'FALSE NEGATIVES: %d' % len(set([(i,p) for i,p in false_negatives]))
        for i,p in sorted(set([(i,p) for i,p in false_negatives]), key = lambda x: x[1]):
            print '%5d %6.2f: %s' % (i,p, tweets[i][1]) 
            
        print '-' * 80
        print 'FALSE POSITIVES: %d' % len(set([(i,p) for i,p in false_positives]))
        for i,p in sorted(set([(i,p) for i,p in false_positives]), key = lambda x: x[1]):
            print '%5d %6.2f: %s' % (i,p, tweets[i][1])

        print '-' * 80
    
    print_confusion_matrix(confusion_matrix)
    
def show_classification_details(test_pattern):
    """Show the inner calculations the classifier uses to classify
        strings containing test_string
    """
    print 'Pattern = "%s"' % test_pattern
    test_data = [t for t in tweets if test_pattern in t[1]]
    train_data = [t for t in tweets if test_pattern not in t[1]]
    print test_data
    model = BayesClassifier(train_data)
    for cls, message in test_data:
        kls, log_odds, ngrams = model.classify(message, True)
        print kls, cls, log_odds
        for k in sorted(ngrams):
            print '%6.3f : %s ' % (k, ngrams[k])    

if __name__ == '__main__':

    import optparse

    parser = optparse.OptionParser(usage = 'Usage: python %prog [options]')
    parser.add_option('-o', '--optimize', action='store_true', dest='optimize', default=False, help='find optimum back-offs and smoothings')
    parser.add_option('-n', '--ngrams', action='store_true', dest='ngrams', default=False, help='show ngrams')
    parser.add_option('-s', '--basic-validate', action='store_true', dest='self_validate', default=False, help='do basic validation')
    parser.add_option('-c', '--cross-validate', action='store_true', dest='cross_validate', default=False, help='full cross-validation')
    parser.add_option('-e', '--show-prediction-error', action='store_true', dest='show_errors', default=False, help='show false positives and false negatives')
    parser.add_option('-m', '--model', action='store_true', dest='model', default=False, help='save calibration model')
    parser.add_option('-t', '--test-string', dest='test_string', default='', help='show ngrams for string')
    
    (options, args) = parser.parse_args()
    
    if not any(options.__dict__.values()): 
        parser.error('No options specified')
 
    tweets = get_labelled_tweets() 
 
    if options.optimize:
        optimize_params(tweets)
       
    if options.ngrams:
        show_ngrams(tweets)
        
    if options.self_validate:
        show_self_validation(tweets)

    if options.cross_validate or options.show_errors:
        show_cross_validation(tweets, options.show_errors)

    if options.test_string:
        show_classification_details(options.test_string)

    if options.model:
        model = BayesClassifier(tweets)
        common.save_model(model)

        