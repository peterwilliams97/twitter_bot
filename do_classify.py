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

print CLASS_STRINGS
print STRING_CLASSES

def get_class(s):
    return STRING_CLASSES.get(s, UNKNOWN)
   
tweets = []
fp = open(CLASS_FILE + '.out', 'rt')
for i,ln in enumerate(fp):
    parts = [pt.strip() for pt in ln.split('|')]
    tweets.append((get_class(parts[0]), parts[1]))
fp.close()

for i,t in enumerate(tweets):
    print '%s | %s' % (CLASS_STRINGS[t[0]], t[1])
    
classifier = BayesClassifier()
classifier.train(tweets)

file(NGRAM_FILE, 'wt').write(str(classifier))
 
    
    



    



