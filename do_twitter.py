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

def E(msg):
    """Log serious errors"""
    full_msg = '%s : %s' % (msg, str(sys.exc_info()[0:2]))
    print full_msg
    logging.error(full_msg)
    time.sleep(1)

def A(user):
    return '@%s' % user
    
RE_PAPERCUT = re.compile(r'paper\s*cut', re.IGNORECASE)
def is_relevant(twitter_status):
    """We are looking for tweets that contain 'papercut'"""
    message = clean_text(twitter_status.text.encode('ascii', 'replace'))
    return RE_PAPERCUT.search(message) is not None

class ScoredTweet:
    """Tweet plus a score
        Tweet info
            id: unique id of tweet
            tm: time of tweet
            user: user name of tweeter
            message: text of tweet
        Score        
            replyable : True if we are really sure the tweeter had a
                paper cut
            sc = is log(odds ratio) of tweet being positive 
    """
    def __init__(self, model, twitter_status):
        # Decode the twitter_status
        tm0 = time.strptime(twitter_status.created_at[:-6], '%a, %d %b %Y %H:%M:%S')
        self._time = time.mktime(tm0)
        self._user = twitter_status._user.screen_name
        self._message = clean_text(twitter_status.text.encode('ascii', 'replace'))
        self._id = twitter_status._id
        
        # Score the decoded status
        positive, self._score =  model.classify(self._message)
        self._replyable = positive and do_label.is_allowed_for_replying(self._message) 

    def __repr__(self):
        return '%-5s|%6.2f|%s"' % (self._replyable, self._score, self.encode_tweet_line())  
        
    def get_tweet_line(self):
        return encode_tweet_line(self._id, self._time, self._user, self._message)
        
    def get_score_line(self): 
        return ' %-5s %6.2f %-15s : "%s"' % (self._replyable, self._score, A(self._user), self._message)  

def load_replied_tweets():
    """Return a list of (id,user) of the tweets already replied to"""
    replied_tweets = []

    try:
        fp = open(REPLIES_FILE, 'rt')
    except IOError:    
        logging.error('Could not open %s', REPLIES_FILE)
        return replied_tweets

    try:    
        for line in fp:
            line = line.rstrip('\n').strip()
            if line:
                id,_,user,_ = decode_tweet_line(line)
                replied_tweets.append((id, user))
    finally:
        fp.close()    
    
    return replied_tweets    
    
def get_replied_users(replied_tweets):
    return set(user.lower() for _,user in replied_tweets)

def get_latest_scored_tweets(api, model, latest_tweet_id): 

    def search_twitter(pattern):
        try:
            results = api.GetSearch(pattern, since_id = latest_tweet_id)
            time.sleep(1)
            return results
        except Exception:
            E(' Twitter api error for search "%s"' %  pattern) 
            return []
    
    results = search_twitter('paper cut') + search_twitter('papercut')
    results = [r for r in results if is_relevant(r)]
    return [ScoredTweet(model, r) for r in results] 
 
def record_tweets(scored_tweets):
    """ Store the tweets in TWEETS_FILE
    """
       
    try:
        fp = open(TWEETS_FILE, 'at')
    except:     
        logging.error('Could not open %s' % TWEETS_FILE)
        return

    try:    
        for tweet in scored_tweets:
            print tweet.get_score_line()
            logging.info(tweet.get_score_line())
            fp.write('%s\n' % tweet.get_tweet_line())
    finally:
        fp.close()
        
if True:
    def read_summary():  
        tweet_num, num_tweets, tm = 0, 0, 0.0
        try:
            text = file(TWEET_SUMMARY_FILE, 'rt').read().strip('\n')
            print 'read_summary:', text
            parts = [p.strip() for p in text.split('|')]
            tweet_num = int(parts[0])
            num_tweets = int(parts[1])
            tm = float(parts[2])
        except:
            E('Could not read %s' % TWEET_SUMMARY_FILE) 
        return tweet_num, num_tweets, tm  
        
    def write_summary(tweet_num, num_tweets, tm):
        parts = tweet_num, num_tweets, tm
        text = ' | '.join([str(p) for p in parts])        
        print 'write_summary:', text
        try:
            file(TWEET_SUMMARY_FILE, 'wt').write(text)
        except:
            E(' Could not save summary')    
        
class Activity:

    SUMMARY_TM_FORMAT = '%I:%M%p %a %d %b %Y' 
    RE_SUMMARY = re.compile(r'I have empathised with (\d+) people since\s(.+)$')
    
    def encode_summary(num_tweets, tm): 
        """
            Twitter has been busier than Liebig St on a Friday afternoon.
            I have empathised with 3 people since 11:43PM Fri 17 Aug 2012
        """
        tm_str = time.strftime(SUMMARY_TM_FORMAT, time.localtime(tm))    
        summary = 'Twitter has been busier than Liebig St on a Friday afternoon. ' + \
                  'I have empathised with %d people since %s''' % (num_tweets, tm_str)
        return summary

    def decode_summary(summary):
        num_tweets, tm = 0, 0.0
        try:
            m = RE_SUMMARY.search(summary)
            num_tweets = int(m.group(1))
            tm = time.mktime(time.strptime(m.group(2), SUMMARY_TM_FORMAT))
        except Exception:
            E(' Could not decode summary "%s"' % summary) 
        return num_tweets, tm
        
    def __init__(self, api):
        self._api = api
        self._last_tweet_num, self._last_num_tweets, self._last_time = read_summary()
        write_summary(self._last_tweet_num, self._last_num_tweets, self._last_time)
  
    def __repr__(self):
        return encode_summary(self._last_num_tweets, self._last_time)
  
    def post_summary_tweet(self, replied_tweets, tweet):
        """Post a summary tweet from time to time.
           
        """
        tweet_num = len(replied_tweets)
        
        # To keep this infrequent, we don't post until we have 
        # exceeded the number of tweets in the last summary post
        if tweet_num <= self._last_tweet_num + self._last_num_tweets:
            return
            
        num_tweets = tweet_num > self._last_tweet_num
        tm = tweet._time
        if False:
            try:
                summary = encode_summary(num_tweets, tm)
                self._api.PostUpdate(summary)
                time.sleep(1)
            except Exception:
                E(' Twitter api error posting summary "%s"' % summary)
             
        parts = tweet_num, num_tweets, tm
        write_summary(tweet_num, num_tweets, tm)        
        self._last_tweet_num, self._last_num_tweets, self._last_time = tweet_num, num_tweets, tm
 

def reply_to_tweets(api, activity, replied_tweets, scored_tweets):

    l_replied_users = get_replied_users(replied_tweets)
    
    try:
        fp = open(REPLIES_FILE, 'at')
    except IOError:    
        logging.error('Could not open %s', REPLIES_FILE)
        return
    try:    
        for tweet in scored_tweets:
            l_message = tweet._message.lower()
            
            # Don't reply to users more than once
            if tweet._user.lower() in l_replied_users:
                logging.info(' skipping: already replied to %s' % tweet._user)
                continue 
            # Don't reply to responses    
            if TWITTER_ME.lower() in l_message:
                logging.info('  skipping:  response "%s"' % tweet._message)
                continue
            # Don't reply to mentions of tweets we have responded to    
            if any(A(u).lower() in l_message for u in l_replied_users):
                logging.info('  skipping: mention: %s:"%s:' % (A(u), tweet._message))
                continue
           
            reply_message = '%s Yes, paper cuts sure do hurt. I hope it gets better soon.' % A(tweet._user)             

            print '  Posting in reply to %s: %s' % (A(tweet._user), str(reply_message))
            logging.info('  Posting in reply to %s: %s' % (A(tweet._user), str(reply_message)))
            
            if False:
                try:
                    api.PostUpdate(reply_message, in_reply_to_status_id=tweet._id)
                    time.sleep(1)
                except Exception:
                    print ' Twitter api error: %s' % str(sys.exc_info()[0:2])
                    logging.error(' Twitter api error: %s' % str(sys.exc_info()[0:2]))
    
            replied_tweets.append((tweet._id, tweet._user))
            fp.write('%s\n' % tweet.get_tweet_line())
            l_replied_users.add(tweet._user.lower())
            
            activity.post_summary_tweet(replied_tweets, tweet)

    finally:        
        fp.close()        

def main_loop(max_duration, replying_enabled):  

    logging.info('max_duration=%d, replying_enabled=%s' % (max_duration, replying_enabled))
    start_time = time.time()
    delay = 0.1
    
    def elapsed(): 
        return time.time() - start_time
        
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
    credentials = dict((m.group(1),m.group(2)) 
        for m in RE_CREDENTIALS.finditer(file(CREDENTIALS_FILE,'rt').read()))
      
    # Get access to Twitter APIs        
    api = twitter.Api(**credentials)
    
    activity = Activity(api)
    
    while elapsed() + delay < max_duration:
        time.sleep(delay)
        
        latest_tweet_id += 1
        scored_tweets = get_latest_scored_tweets(api, model, latest_tweet_id) 
        
        if scored_tweets:
            scored_tweets.sort(key = lambda t: (not t._replyable, -t._score, t._id)) 
            latest_tweet_id = max([t._id for t in scored_tweets])
            file(LATEST_FILE, 'wt').write(str(latest_tweet_id))
            record_tweets(scored_tweets)

            replyable_tweets = [t for t in scored_tweets if t._replyable]
            # Reply to all the tweeets that we should reply to 
            if replying_enabled and replyable_tweets:
                reply_to_tweets(api, activity, replied_tweets, replyable_tweets)
        
        delay = 10 if scored_tweets else delay * 2
        delay = max(10, min((abs(elapsed() - max_duration)/10), delay))
        
        msg = 'Found %3d replyable of %3d relevant results, latest_id=%d, sleeping %5.1f sec, running %4d sec' % (
                    len([t for t in scored_tweets if t._replyable]), 
                    len(scored_tweets), latest_tweet_id,
                    delay, elapsed())
        print msg
        logging.info(msg)

if __name__ == '__main__':
    logging.info('-' * 80)
    logging.info('Starting %s' % str(sys.argv[0]))
    main_loop(10 * 60 * 60, True)
    
    