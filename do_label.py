import twitter, os, time, sys, re
from common import *

NEGATIVES = [
'Humans are the only creatures on earth that will cut down trees'
]

def get_class(message):
    if any(n in message for n in NEGATIVES):
        return False
    return None


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
   

# Read the tweets
tweets = []
fp = open(TWEETS_FILE, 'rt')
for i,ln in enumerate(fp):
    ln = ln.strip('\n')
    print  ln.split(',')
    _,_,_,message = [pt.strip() for pt in ln.split('|')]
    tweets.append([get_class(message), message])
fp.close()

fp = open(CLASS_FILE, 'rt')
for i,ln in enumerate(fp):
    parts = [pt.strip() for pt in ln.split('|')]
    tweets[i][0] = get_class(parts[0])
fp.close()

fp = open(CLASS_FILE + '.out', 'wt')
for i,t in enumerate(tweets):
    fp.write('%s | %s\n' % (CLASS_STRINGS[t[0]], t[1]))
fp.close()

fp = open(CLASS_FILE + '.out', 'rt')
for i,ln in enumerate(fp):
    ln = ln.strip('\n')
    print '%3d : %s' % (i, ln)
fp.close()

    



