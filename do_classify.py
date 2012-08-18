import twitter, os, time, sys, re
from common import *
from BayesClassifier import BayesClassifier

UNKNOWN = -1    
CLASS_STRINGS = {
    False: 'n',
    True: 'y',  
    UNKNOWN: '?'
}
STRING_CLASSES = dict([(v,k) for k,v in CLASS_STRINGS.items()])

RE_USER = re.compile(r'@\w+')
RE_HTTP = re.compile(r'http://\S+')

def clean(message):
    message = RE_USER.sub('[TAG_USER]', message)
    message = RE_HTTP.sub('[TAG_LINK]', message)
    return message


def get_class(s):
    return STRING_CLASSES.get(s, UNKNOWN)
   
tweets = []
fp = open(CLASS_FILE, 'rt')
for i,ln in enumerate(fp):
    parts = [pt.strip() for pt in ln.split('|')]
    cls, message = get_class(parts[0]), parts[1]
    if cls in set([False,True]):
        tweets.append((cls, clean(message)))
fp.close()

    
classifier = BayesClassifier()
classifier.train(tweets)

file(NGRAM_FILE, 'wt').write(str(classifier))

ratings = [(classifier.classify(t[1]), t) for t in tweets]
ratings.sort()
ratings.reverse()

fp = open(VALIDATION_FILE, 'wt')
for r in ratings:
    fp.write('%s\n' % str(r))
fp.close()  

def make_score():
    return dict([((a,p),0) for p in (False,True) for a in (False,True)])

def get_test_score(training_tweets, test_tweets, test_indexes):
    classifier = BayesClassifier()
    classifier.train(training_tweets)
    score = make_score()
    fp = []
    fn = []
    for i,t in enumerate(test_tweets):
        a = t[0]
        p, posterior = classifier.classify(t[1])
        score[(a,p)] += 1
        if p != a:
            if p: fp.append(test_indexes[i])
            else: fn.append(test_indexes[i])
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
    
confusion_matrix,false_positives,false_negatives = cross_validate(tweets, 10)
print confusion_matrix
print false_positives
print false_negatives
for i in sorted(set(false_positives)):
    print '%3d : %s' % (i, tweets[i][1])
    
    



    



