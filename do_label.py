import twitter, os, time, sys, re, shutil
from common import *
"""
    We classify tweets as one of 
       - True : We should reply to the tweet
       - False: We should not reply to the tweets
       - UNKNOWN: We don't know
       
    In all our text files we encode True/False/Unknown as 
        
    
""" 
CLASS_STRINGS = {
    True: 'y',  
    False: 'n',
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
        cls,log_odds = model.classify(message)
    else:
        cls,log_odds = UNKNOWN, 0.0
    return AUTO_CLASS_STRINGS[cls]

def main():
    
    # Lastest labelled tweet id (an integer) is stored as text in LATEST_CLASS_FILE
    # We use to prevent re-reading tweets
    latest_labelled_tweet_id = int(file(LATEST_CLASS_FILE, 'rt').read().strip())  if os.path.exists(LATEST_CLASS_FILE) else 0    
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
            continue
        id = int(id_s)
        if id <= latest_labelled_tweet_id:
            continue
        if not is_allowed_for_training(message):
            continue
        kls = get_class_str(model, message)
        #print kls, [id,tm,user,message]
            
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

    



