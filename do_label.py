import twitter, os, time, sys, re, shutil
from common import *

# This list is used to exclude whole tweets that have already been seen
# It is NOT used to exclude phrases like 'Sandpaper kisses, paper cut bliss'
# These strings should be added t screen new tweets as well
EXCLUSIONS = [
    'only creatures on earth that will cut down trees',
    'one final moment of glorious revenge',
    'Paper cut. I don\'t like it lmao',
    'holy cow balls Harry',
    'receiving a papercut whilst signing his',
    'The Gym Leader used a full restore.'
]

def allowed(message):
    return not any(e in message for e in EXCLUSIONS)

CLASS_STRINGS = {
    False: 'n',
    True: 'y',  
    UNKNOWN: '?'
}
STRING_CLASSES = dict([(v,k) for k,v in CLASS_STRINGS.items()])

def get_class(s):
    return STRING_CLASSES.get(s, UNKNOWN)
    
# Lastest labelled tweet id (an integer) is stored as text in LATEST_CLASS_FILE
# We use to prevent re-reading tweets
latest_labelled_tweet_id = int(file(LATEST_CLASS_FILE, 'rt').read().strip()) if os.path.exists(LATEST_CLASS_FILE) else 0    
previous_tweet_id = latest_labelled_tweet_id
   
# Read the tweets
labelled_messages = []
fp = open(TWEETS_FILE, 'rt')
for line in fp:
    line = line.strip('\n').strip()
    if not line:
        continue
    id_s,tm,user,message = [pt.strip() for pt in line.split('|')]
    id = int(id_s)
    if id <= latest_labelled_tweet_id:
        continue
    if not allowed(message):
        continue
    print [id,tm,user,message]
    labelled_messages.append([get_class(message), message])
    latest_labelled_tweet_id = max(id, latest_labelled_tweet_id)
fp.close()

print 'loaded %d labelled_messages' % len(labelled_messages)
print 'before: latest_labelled_tweet_id=%d' % previous_tweet_id
print 'after:  latest_labelled_tweet_id=%d' % latest_labelled_tweet_id

if False:
    fp = open(CLASS_FILE, 'rt')
    for i,ln in enumerate(fp):
        parts = [pt.strip() for pt in ln.split('|')]
        labelled_messages[i][0] = get_class(parts[0])
    fp.close()

shutil.copyfile(CLASS_FILE, '%s.%d' % (CLASS_FILE, previous_tweet_id))

     
fp = open(CLASS_FILE, 'at')
for i,t in enumerate(labelled_messages):
    fp.write('%s | %s\n' % (CLASS_STRINGS[t[0]], t[1]))
fp.close()
file(LATEST_CLASS_FILE, 'wt').write(str(latest_labelled_tweet_id))

if False:
    fp = open(CLASS_FILE + '.out', 'rt')
    for i,ln in enumerate(fp):
        ln = ln.strip('\n')
        print '%3d : %s' % (i, ln)
    fp.close()

    



