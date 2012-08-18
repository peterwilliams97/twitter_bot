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
    message = RE_USER.sub('', message)
    message = RE_HTTP.sub('', message)
    return message

if False:    
    message = 'so in simple terms  http://t.co/WVPZ0yOv'
    print clean(message)
    exit()   

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

if False:
    for i,t in enumerate(tweets):
        print '%s | %s' % (CLASS_STRINGS[t[0]], t[1])
    
classifier = BayesClassifier()
classifier.train(tweets)

file(NGRAM_FILE, 'wt').write(str(classifier))
 
    
    



    



