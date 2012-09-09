from __future__ import division
"""
    Peform various statistical tests on the labelled tweets in CLASS_FILE
""" 
import sys, re, random

# Our shared modules
from BayesClassifier import BayesClassifier
import common, definitions, filters

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

do_filter = False    
def get_test_score(training_tweets, test_tweets, test_indexes):
    model = BayesClassifier(training_tweets)

    score = get_empty_score()
    fp = []
    fn = []
    for i,t in enumerate(test_tweets):
        a = t[0]
        p, log_odds = model.classify(t[1])
        if do_filter:
            p = p and filters.is_allowed_for_replying(t[1])
        score[(a,p)] += 1
        if p != a:
            if p: fp.append((test_indexes[i], log_odds))
            else: fn.append((test_indexes[i], log_odds))
    return score, fp, fn

def cross_validate(tweets, num_folds):
    """Perform num_folds-fold cross-validations on tweets and return
        confusion_matrix, false_positives, false_negatives
    """    
    confusion_matrix = get_empty_score()
    false_positives = []
    false_negatives = []
    boundaries = [int(i*len(tweets)/num_folds) for i in range(num_folds + 1)]
    for i in range(1, len(boundaries)):
        begin,end = boundaries[i-1],boundaries[i]
        test_tweets = tweets[begin:end]
        training_tweets = tweets[:begin] + tweets[end:]
        score,fp,fn = get_test_score(training_tweets, test_tweets, range(begin,end))
        for k in score.keys(): confusion_matrix[k] += score[k]
        false_positives += fp   
        false_negatives += fn  
    return confusion_matrix, sorted(false_positives), sorted(false_negatives)
  
def get_precision(matrix):
    return matrix[(True,True)]/(matrix[(True,True)] + matrix[(False,True)])

def get_recall(matrix):
    return matrix[(True,True)]/(matrix[(True,True)] + matrix[(True, False)])  
    
def get_f(matrix):
    return 2.0/(1.0/get_precision(matrix) + 1.0/get_recall(matrix))

ALPHA = 0.9
assert 0.0 <= ALPHA <= 1.0, 'ALPHA = %f is invalid' % ALPHA
def get_opt_target(matrix):
    """The objective function that we aim to maximize"""
    return 1.0/(ALPHA/get_precision(matrix) + (1.0-ALPHA)/get_recall(matrix)) 

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

def matrix_str(matrix):
    total = sum([matrix[a,p] for p in (False,True) for a in (False,True)])
    vals = ', '.join(['%4.1f' % (matrix[a,p]/total * 100.0)
                    for p in (False,True) for a in (False,True)])
    return '{%s}' % vals
    
def arr_str(arr):
    vals = ','.join(['%6.3f' % x for x in arr])
    return '[%s]' % vals    

def optimize_params(tweets):
    from scipy import optimize
    
    def get_params(x):
        return (x[0], 
            #BayesClassifier.smooth_bigram,
            #BayesClassifier.smooth_trigram,
            x[1], x[2],
            x[3], x[4], x[5]
            )  
    
    def func(x):
        BayesClassifier.set_params(*get_params(x))
        matrix,_,_ = cross_validate(tweets, 10)
        f = -get_opt_target(matrix)
        print ' %.4f %s %s' % (-f, matrix_str(matrix), 
            arr_str(BayesClassifier.get_params())
            )
        return f

    x0 = [
        BayesClassifier.smooth_unigram,
        BayesClassifier.smooth_bigram,
        BayesClassifier.smooth_trigram, 
        BayesClassifier.backoff_bigram, 
        BayesClassifier.backoff_trigram,
        BayesClassifier.threshold
    ]
    
    print 'ALPHA = %.3f' % ALPHA
    x = optimize.fmin(func, x0)
    print '^' * 80
    print -func(x0), x0
    print -func(x), list(x)
    
    # Reinstall the best params
    BayesClassifier.set_params(*get_params(x))
    matrix,_,_ = cross_validate(tweets, 10)
    
    print '    # Precision = %.3f, Recall = %.3f, F1 = %.3f' % (
        get_precision(matrix), get_recall(matrix), get_f(matrix))  
    for k,v in zip(BayesClassifier.get_param_names(), BayesClassifier.get_params()):
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
            percentage_matrix[a,p] = '%2d%%' % int(round(confusion_matrix[a,p]/total * 100.0))
            
    print_matrix(confusion_matrix)  
    print 'Total = %d' % total   
    print
    print_matrix(percentage_matrix) 
    print 'Precision = %.3f, Recall = %.3f, F1 = %.3f' % (
        get_precision(confusion_matrix), get_recall(confusion_matrix), get_f(confusion_matrix))    
    print

def show_cross_validation(tweets, show_errors):
    
    confusion_matrix, false_positives, false_negatives = cross_validate(tweets, 10)

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
    
    parser.add_option('-n', '--ngrams', action='store_true', dest='ngrams', default=False, help='show ngrams')
    parser.add_option('-s', '--self-validate', action='store_true', dest='self_validate', default=False, help='do self=validation')
    parser.add_option('-c', '--cross-validate', action='store_true', dest='cross_validate', default=False, help='do cross-validation')
    parser.add_option('-e', '--show-errors', action='store_true', dest='show_errors', default=False, help='show false positives and false negatives')
    parser.add_option('-t', '--test-string', dest='test_string', default='', help='show ngrams for string')
    parser.add_option('-o', '--optimize', action='store_true', dest='optimize', default=False, help='find optimum threshold, back-offs and smoothings')
    parser.add_option('-m', '--model', action='store_true', dest='model', default=False, help='save calibration model')
    parser.add_option('-f', '--filter', action='store_true', dest='filter', default=False, help='apply filter')
    do_filter
    
    (options, args) = parser.parse_args()
    
    if not any(options.__dict__.values()): 
        parser.error('No options specified')
 
    tweets = get_labelled_tweets() 
 
    do_filter = options.filter

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

        