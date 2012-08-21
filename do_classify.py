import twitter, os, time, sys, re, pickle
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
        cls, message = get_class(parts[0]), parts[1]
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
        p, log_odds, ngrams = model.classify(t[1])
        score[(a,p)] += 1
        if p != a:
            if p: fp.append((test_indexes[i], log_odds, ngrams))
            else: fn.append((test_indexes[i], log_odds, ngrams))
            #if p:  print '>>>', test_indexes[i], p, t
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
  
def print_confusion_matrix(confusion_matrix):  
    BAR = '-' * 5
    print '%5s | %5s | %5s' % ('', False, True)
    print '%5s + %5s + %5s' % (BAR, BAR, BAR)  
    print '%5s | %5s | %5s' % (False, confusion_matrix[(False,False)], confusion_matrix[(False,True)]) 
    print '%5s + %5s + %5s' % (BAR, BAR, BAR)  
    print '%5s | %5s | %5s' % (True,  confusion_matrix[(True,False)],  confusion_matrix[(True,True)]) 
    print '%5s + %5s + %5s' % (BAR, BAR, BAR)  

def validate_full(tweets, detailed):
    
    confusion_matrix,false_positives,false_negatives = cross_validate(tweets, 10)

    #print [i for i,p,g in false_positives]
    #print [i for i,p,g in false_negatives]

    print '-' * 80
    print 'FALSE NEGATIVES: %d' % len(set([(i,p) for i,p,_ in false_negatives]))
    for i,p in sorted(set([(i,p) for i,p,_ in false_negatives]), key = lambda x: -x[1]):
        print '%5d %6.2f: %s' % (i,p, tweets[i][1]) 
        
    print '-' * 80
    print 'FALSE POSITIVES: %d' % len(set([(i,p) for i,p,_ in false_positives]))
    for i,p in sorted(set([(i,p) for i,p,_ in false_positives]), key = lambda x: -x[1]):
        print '%5d %6.2f: %s' % (i,p, tweets[i][1])

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
    tweets = get_labelled_tweets() 
    print '=' * 80
    validate_basic(tweets)
    print '=' * 80
    validate_full(tweets, False)

    save_model(tweets)
    
    



