import twitter, os, time, sys, re, shutil
from common import *
import do_classify

# This list is used to exclude whole tweets that have already been seen
# It is NOT used to exclude phrases like 'Sandpaper kisses, paper cut bliss'
# These strings should be added t screen new tweets as well
# Also
#   RT
EXCLUSIONS = [
    'only creatures on earth that will cut down trees',
    'one final moment of glorious revenge',
    'Paper cut. I don\'t like it lmao',
    'holy cow balls Harry',
    'receiving a papercut whilst signing his',
    'The Gym Leader used a full restore.'
]

def allowed(message):
    return not any(e in message for e in EXCLUSIONS) \
        and message.lower()[:2] != 'rt'

CLASS_STRINGS = {
    False: 'n',
    True: 'y',  
    UNKNOWN: '?'
}
STRING_CLASSES = dict([(v,k) for k,v in CLASS_STRINGS.items()])

    
# Lastest labelled tweet id (an integer) is stored as text in LATEST_CLASS_FILE
# We use to prevent re-reading tweets
latest_labelled_tweet_id = int(file(LATEST_CLASS_FILE, 'rt').read().strip()) if os.path.exists(LATEST_CLASS_FILE) else 0    
previous_tweet_id = latest_labelled_tweet_id
   
   
AUTO_CLASS_STRINGS  = {
    False: 'N',
    True: 'Y',  
    UNKNOWN: '?'
}  
classifier = do_classify.get_classifier_for_labelled_tweets()

def get_class_str(message):
    if classifier:
        cls,posterior,llk = classifier.classify(message)
    else:
        cls,posterior,llk = UNKNOWN, 0.0, None
    return AUTO_CLASS_STRINGS[cls]
   
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
    kls = get_class_str(message)
    print kls, [id,tm,user,message]
        
    labelled_messages.append([kls, message])
    latest_labelled_tweet_id = max(id, latest_labelled_tweet_id)
fp.close()

print 'added %d labelled_messages' % len(labelled_messages)
print 'before: latest_labelled_tweet_id=%d' % previous_tweet_id
print 'after:  latest_labelled_tweet_id=%d' % latest_labelled_tweet_id

if latest_labelled_tweet_id == previous_tweet_id:
    print 'Nothing to do'
    exit()

 
# Save the current labelled data file
shutil.copyfile(CLASS_FILE, '%s.%d' % (CLASS_FILE, previous_tweet_id))

# Add the new entries to the labelled data file
fp = open(CLASS_FILE, 'at')
for i,t in enumerate(labelled_messages):
    fp.write('%s | %s\n' % (t[0], t[1]))
fp.close()

# Update the latest labelled entry id
file(LATEST_CLASS_FILE, 'wt').write(str(latest_labelled_tweet_id))



    



