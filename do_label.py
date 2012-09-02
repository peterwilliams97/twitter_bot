import twitter, os, time, sys, re, shutil
# Our shared modules
import common, definitions, filters  

def update_class_file():
    """We store list of labelled tweets in *.cls files in the format
            class label | message
        e.g.
            n | If I see one more back to school commercial I'm giving my eyes a paper cut.
            y | i got lemon on my finger and it stings .-. stupid paper cut -.-
            
        (Only the tweet text is stored here. The other tweet infornation
         is not stored as we used only the tweet text for classification)  
             
        common.LATEST_CLASS_FILE (see common.py for actual name) is the
            file where we keep our most up-to-list of labelled tweets
         
        This function updates common.LATEST_CLASS_FILE using common.TWEETS_FILE,
        which contains all the tweets that have undergone simple screening and
        we have saved.
        
        It also guesses labels for each new tweet using the latest classification
        model.
        
        (We track the tweet id of the latest tweet in common.LATEST_CLASS_FILE)
    """
    
    # The lastest labelled tweet id (an integer) is stored as text in LATEST_CLASS_FILE
    latest_labelled_tweet_id = int(file(common.LATEST_CLASS_FILE, 'rt').read().strip()) if os.path.exists(common.LATEST_CLASS_FILE) else 0    
    previous_tweet_id = latest_labelled_tweet_id
      
    # Read the classification model. This will be used to guess tweet classifications
    model = common.load_model()
         
    # Read the tweets from TWEETS_FILE, label them and store them
    # in labelled_messages
    labelled_messages = []
    fp = open(common.TWEETS_FILE, 'rt')
    for line in fp:
        line = line.strip(' \n')
        
        # Skip empty lines
        if not line:
            continue
            
        # Skip incorrectly formatted lines
        try:    
            id_s,_,_,message = [pt.strip() for pt in line.split('|')]
            id = int(id_s)
        except ValueError:
            print 'ValueError', line
            continue
        
        # Skip tweets we have already saved
        if id <= latest_labelled_tweet_id:
            continue
            
        # Filter out messages that are not even allowed for training    
        if not filters.is_allowed_for_training(message):
            continue
        cls,_ = model.classify(message)    
                   
        labelled_messages.append([definitions.AUTO_CLASSES_LABELS[cls], message])
        latest_labelled_tweet_id = max(id, latest_labelled_tweet_id)
    fp.close()

    print 'found %d new tweets' % len(labelled_messages)
    print 'before: latest_labelled_tweet_id=%d' % previous_tweet_id
    print 'after:  latest_labelled_tweet_id=%d' % latest_labelled_tweet_id

    if latest_labelled_tweet_id == previous_tweet_id:
        print 'Nothing to do'
        exit()
     
    # Save the current labelled data file
    shutil.copyfile(common.CLASS_FILE, '%s.%d' % (common.CLASS_FILE, previous_tweet_id))

    # Add the new entries to the labelled data file
    fp = open(common.CLASS_FILE, 'at')
    for i,t in enumerate(labelled_messages):
        fp.write('%s | %s\n' % (t[0], t[1]))
    fp.close()
    
    print 'Added %d new labelled messages to %s' % (len(labelled_messages), common.CLASS_FILE)

    # Update the latest labelled entry id
    file(common.LATEST_CLASS_FILE, 'wt').write(str(latest_labelled_tweet_id))

if __name__ == '__main__':
    update_class_file()

    



