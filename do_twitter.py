"""
    Uses 
    http://code.google.com/p/python-twitter/
"""
import twitter, os, time, sys, re

# Get all the file names *_FILE
from common import *
import do_classify, do_label

import logging
logging.basicConfig(filename = LOG_FILE, 
            level = logging.INFO,
            format = '%(asctime)s %(message)s')

def decode_result(result):
    """Convert a result returned from the Twitter API
        to id, tm, user, message
            id: tweet id (globally unique integer)
            tm: time of tweet
            user: username of tweeter
            message: text of tweet
    """
    tm0 = time.strptime(result.created_at[:-6], '%a, %d %b %Y %H:%M:%S')
    tm = time.mktime(tm0)
    user = result.user.screen_name
    message = result.text.encode('ascii', 'replace')
    id = result.id
    return id, tm, user, message 

print '-' * 80
RE_PAPERCUT = re.compile(r'paper\s*cut', re.IGNORECASE)
def is_relevant(message):
    """We are looking for tweets that contain 'papercut'"""
    return RE_PAPERCUT.search(message) is not None

def is_replyable(model, message):
    """Return replyable,log_odds
       - replyable = True if we are really sure the tweeter had a
                paper cut
       - log_odds = is log(odds ratio) of tweet being positive 
    """
    allowed = do_label.is_allowed_for_replying(message)
    positive,log_odds,_ =  model.classify(message)
    return allowed and positive, log_odds


def load_replied_tweets():
    """Return a list of (id,user) of the tweets already replied to"""
    replied_tweets = []
      
    try:
        fp = open(REPLIES_FILE, 'rt')
    except IOError:    
        logging.error('Could not open %s', REPLIES_FILE)
        return replied_tweets
    
#try:
    for line in fp:
        line = line.rstrip('\n').strip()
        if line:
            id,tm,_,_ = decode_tweet_line(line)
            replied_tweets.append((id, user))
    fp.close()    
#except:
#    print 'REPLIES_FILE "%s" does not exist' % REPLIES_FILE
    
    return replied_tweets    
    
def get_replied_users(replied_tweets):
    return set(user.lower() for _,user in replied_tweets)

def A(user):
    return '@%s' % user.lower()
    
def reply_to_tweets(api, replied_tweets, replyable_tweets):

    l_replied_users = get_replied_users(replied_tweets)
    
    try:
        fp = open(REPLIES_FILE, 'at')
    except IOError:    
        logging.error('Could not open %s', REPLIES_FILE)
        return
    try:    
        for id, tm, user, message in replyable_tweets:
            l_message = message.lower()
            
            # Don't reply to users more than once
            if user in l_replied_users:
                continue 
            # Don't reply to responses    
            if TWITTER_ME.lower() in message:
                continue
            # Don't reply to mentions of tweets we have responded to    
            if any(A(u) in l_message for u in l_replied_users):
                print "Skipping because it's a mention: @%s - %s" % (u, message)
                continue
            
            # !@#$
            if 'peter' in user or 'alec' in user:
                reply_message = '%s Yes, paper cuts sure do hurt. I hope it gets better soon.' % A(user)             
                print 'Incoming: %s' % str(message)
                print 'Posting in reply to @%s: %s' % (user, str(reply_message))
                api.PostUpdate(reply_message, in_reply_to_status_id=id)
                
            replied_tweets.append((id, user))
            fp.write('%s\n' % encode_tweet_line(id, tm, user, message))
            
            time.sleep(1)
    #except Exception:
    #    print 'Unexpected error:', sys.exc_info()[0:2]   
    finally:        
        fp.close()

def main_loop(do_reply):  

    logging.info('Starting '+ sys.argv[0])

    # Load the calibration model first
    model = do_classify.load_model()
    
    # Lastest tweet id (an integer) is stored as text in LATEST_FILE
    # We use to prevent re-reading tweets
    latest_tweet_id = int(file(LATEST_FILE, 'rt').read().strip()) if os.path.exists(LATEST_FILE) else 0
    logging.info('latest_tweet_id=%d' % latest_tweet_id)
    
    # Load the tweets replied to
    replied_tweets = load_replied_tweets()

    # Credentials are stored in CREDENTIALS_FILE as text lines of key='value' 
    # The keys are: consumer_key, consumer_secret, access_token_key, access_token_secret 
    RE_CREDENTIALS = re.compile(r"(\w+)='([^']+)'")
    credentials = dict((m.group(1),m.group(2)) for m in RE_CREDENTIALS.finditer(file(CREDENTIALS_FILE,'rt').read()))
      
    # Get access to Twitter APIs        
    api = twitter.Api(**credentials)

    while True:
        # perform the search
        # until no matching tweets are found
        latest_tweet_id += 1
        results1 = api.GetSearch('paper cut', since_id = latest_tweet_id)
        if False:
            time.sleep(1)
            results2 = api.GetSearch('papercut', since_id = latest_tweet_id)
        else:
            results2 = []
        results = results1 + results2 
        print 'Found %d results = %d + %d' % (len(results), len(results1), len(results2))
        if len(results) == 0:
            logging.info(' No more matching tweets')
            print ' No more matching tweets. Quitting.'
            return
            
        tweets = [decode_result(r) for r in results]    
        tweets.sort(key = lambda t: t[0])
        
        num_relevant = 0 
        replyable_tweets = []
        # Store the tweets in TWEETS_FILE
        fp = open(TWEETS_FILE, 'at')
        if not fp:
            logging.error('Could not open %s' % TWEETS_FILE)
        assert fp, 'Could not open %s' % TWEETS_FILE
        for i,t in enumerate(tweets):
            id, tm, user, message = t
            if is_relevant(message):
                line = encode_tweet_line(id, tm, user, message)
                do_reply,score = is_replyable(model, message)
                scored_line = '%7s %6.2f : %s' % (do_reply, score, message)
                print scored_line
                fp.write('%s\n' % scored_line)
                num_relevant += 1
                if do_reply:
                    replyable_tweets.append((id, tm, user, message))
        fp.close()
        
        latest_tweet_id = max([x.id for x in results])  

        file(LATEST_FILE, 'wt').write(str(latest_tweet_id))
        logging.info(' Added %3d relevant of %3d results, latest_id=%d' % (
                 num_relevant, len(results), latest_tweet_id))
                 
        logging.info(' %d replyable tweets' % len(replyable_tweets))
        print ' %d replyable tweets' % len(replyable_tweets)
        if do_reply:
            # Reply to all the tweeets that we should reply to 
            if replyable_tweets:
                print ' About to reply to %d tweets' % len(replyable_tweets)
                reply_to_tweets(api, replied_tweets, replyable_tweets)
            else:
                print ' No tweets to reply to'
        time.sleep(10)

      
if __name__ == '__main__':
    main_loop(True)
    
    