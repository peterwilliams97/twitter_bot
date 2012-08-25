import twitter, os, time, sys, re, shutil
from common import *
import do_classify

# This list is used to exclude whole tweets that have already been seen
# It is NOT used to exclude phrases like 'Sandpaper kisses, paper cut bliss'
# These strings should be added t screen new tweets as well
# Also
#   RT
TRAINING_EXCLUSIONS = [
    #'only creatures on earth that will cut down trees',
    #'one final moment of glorious revenge',
    #'Paper cut. I don\'t like it lmao',
    #'holy cow balls Harry',
    #'receiving a papercut whilst signing his',
    #'The Gym Leader used a full restore.',
    #'Linkin',
]

REPLYING_EXCLUSION = [
    'only creatures on earth that will cut down trees',
    'one final moment of glorious revenge',
    'Paper cut. I don\'t like it lmao',
    'holy cow balls Harry',
    'receiving a papercut whilst signing his',
    'The Gym Leader used a full restore.',
    'Linkin',
    'LOL'       # To be safe 
    'Sandpaper kisses',
    'paper cut bliss',
    'Bleeds to death',
    'Robin van Persie',
    'hand sanitizer',
    'glorious',
    'revenge',   
    'cruciatus'
    'Papercut_Dolls',
    'birth',
    '@papercut',
    'nigger', 
    'nigga',
    'cunt',  
    'death'
    
   
] 

L_TRAINING_EXCLUSIONS = [e.lower() for e in TRAINING_EXCLUSIONS]
L_REPLYING_EXCLUSION = [e.lower() for e in REPLYING_EXCLUSION]

RE_RT = re.compile(r'\brt(:|\b)')
RE_LOL = re.compile(r'\blols?\b')
RE_EYE = re.compile(r'my\s+eye')  # I think I have a paper cut I my eye.

if False:
    tests = ['rt message', 'log rt:message', 
        'lol rt: message', 'rt: message', 'rt hi',
        'dirt', 'rtere']
    for t in tests:
        print t, RE_RT.search(t) is not None
    tests = ['lol papercut', 'hi lol x', 'hollow']  
    for t in tests:
        print t, RE_LOL.search(t) is not None  
    exit()

def is_allowed_for_training(message):
    l_message = message.lower().strip()
    return not any(e in l_message for e in L_TRAINING_EXCLUSIONS) \
        and not RE_RT.search(l_message)

def is_allowed_for_replying(message): 
    if not is_allowed_for_training(message):
        return False
    l_message = message.lower().strip()
    return not any(e in l_message for e in L_REPLYING_EXCLUSION) \
        and not RE_LOL.search(l_message) \
        and not RE_EYE.search(l_message) \
        and message[0] != '"' 
        

CLASS_STRINGS = {
    False: 'n',
    True: 'y',  
    UNKNOWN: '?'
}
STRING_CLASSES = dict([(v,k) for k,v in CLASS_STRINGS.items()])

AUTO_CLASS_STRINGS  = {
    False: 'N',
    True: 'Y',  
    UNKNOWN: '?'
}  

def get_class_str(model, message):
    if model:
        cls,log_odds,llk = model.classify(message)
    else:
        cls,log_odds,llk = UNKNOWN, 0.0, None
    return AUTO_CLASS_STRINGS[cls]

def main():
    
    # Lastest labelled tweet id (an integer) is stored as text in LATEST_CLASS_FILE
    # We use to prevent re-reading tweets
    latest_labelled_tweet_id = int(file(LATEST_CLASS_FILE, 'rt').read().strip()) if os.path.exists(LATEST_CLASS_FILE) else 0    
    previous_tweet_id = latest_labelled_tweet_id
      
    # Read the classification mode
    model = do_classify.get_classifier_for_labelled_tweets()
         
    # Read the tweets
    labelled_messages = []
    fp = open(TWEETS_FILE, 'rt')
    for line in fp:
        line = line.strip('\n').strip()
        if not line:
            continue
        try:    
            id_s,tm,user,message = [pt.strip() for pt in line.split('|')]
        except ValueError:
            print 'ValueError', line
            exit()
        id = int(id_s)
        if id <= latest_labelled_tweet_id:
            continue
        if not is_allowed_for_training(message):
            continue
        kls = get_class_str(model, message)
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

if __name__ == '__main__':
     main()

    



