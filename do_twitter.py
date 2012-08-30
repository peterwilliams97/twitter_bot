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

def log_sys_err(msg):
    """Log serious errors with print system exceptions"""
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

"""
-- "Wed, 29 Aug 2012 09:29:01 +0000" 1346196541
-- "Wed, 29 Aug 2012 09:20:33 +0000" 1346196033
-- "Wed, 29 Aug 2012 09:10:28 +0000" 1346195428
-- "Wed, 29 Aug 2012 09:13:41 +0000" 1346195621
-- "Wed, 29 Aug 2012 09:09:06 +0000" 1346195346
-- "Wed, 29 Aug 2012 09:08:03 +0000" 1346195283
-- "Wed, 29 Aug 2012 09:07:30 +0000" 1346195250
-- "Wed, 29 Aug 2012 08:58:31 +0000" 1346194711
-- "Wed, 29 Aug 2012 08:15:50 +0000" 1346192150
-- "Wed, 29 Aug 2012 08:06:22 +0000" 1346191582
-- "Wed, 29 Aug 2012 07:49:31 +0000" 1346190571
-- "Wed, 29 Aug 2012 07:44:50 +0000" 1346190290
-- "Wed, 29 Aug 2012 07:41:31 +0000" 1346190091
-- "Wed, 29 Aug 2012 07:30:26 +0000" 1346189426
-- "Wed, 29 Aug 2012 07:08:28 +0000" 1346188108
-- "Wed, 29 Aug 2012 07:08:27 +0000" 1346188107
-- "Wed, 29 Aug 2012 07:06:27 +0000" 1346187987
-- "Wed, 29 Aug 2012 07:02:11 +0000" 1346187731
"""
from datetime import datetime
LOCAL_TIME_DELTA = datetime.now() - datetime.utcnow()
SUMMARY_TM_FORMAT = '%I:%M%p %a %d %b' 
def get_local_time_str(tm):
    gmt = datetime(*time.localtime(tm)[:6])
    gmt += LOCAL_TIME_DELTA
    return gmt.strftime(SUMMARY_TM_FORMAT)

class ScoredTweet:
    """Tweet plus a score
        Tweet info
            _id: unique id of tweet
            _time: time of tweet
            _user: user name of tweeter
            _message: text of tweet
        Score        
            _replyable : True if we are really sure the tweeter had a
                paper cut
            _score: log(odds ratio) of tweet being positive 
    """
    def __init__(self, model, twitter_status):
        # Decode the twitter_status
        tm0 = time.strptime(twitter_status.created_at[:-6], '%a, %d %b %Y %H:%M:%S')
        self._time = time.mktime(tm0)
        self._user = twitter_status._user.screen_name
        self._message = clean_text(twitter_status.text.encode('ascii', 'replace'))
        self._id = twitter_status._id
        
        print '-- "%s" %d' % (twitter_status.created_at, self._time) 
        
        # Score the decoded status
        positive, self._score =  model.classify(self._message)
        self._replyable = positive and do_label.is_allowed_for_replying(self._message) 

    def __repr__(self):
        return '%-5s|%6.2f|%s"' % (self._replyable, self._score, self.get_tweet_line())  
        
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
            log_sys_err(' Twitter api error for search "%s"' %  pattern) 
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

class Activity:
    """Activity record
        _api : Twitter api instance
        _last_reply_num: The number of replies we had made the last time we tweeted a summary 
        _reply_delta: The min number of replies between summary tweets 
        _last_time: The time we last made a summary tweet
    """
  
    SUMMARY_TM_FORMAT = '%I:%M%p %a %d %b %Y' 
    
    @staticmethod
    def encode_summary(tweet_delta, tm): 
        """Write tweet_delta=3 tm=11:43PM Fri 17 Aug 2012 as 
        'Twitter has been busier than Liebig St on a Friday afternoon.
            I have empathised with 3 people since 11:43PM Fri 17 Aug 2012'
        """
        tm_str = get_local_time_str(tm)
        return 'Twitter has been busier than Liebig St on a Friday afternoon. ' + \
                  'I have empathised with %d people since %s.''' % (tweet_delta, tm_str)

    @staticmethod
    def read_activity():  
        tweet_num, tweet_delta, tm = 0, 0, 0.0
        try:
            text = file(ACTIVITY_FILE, 'rt').read().strip('\n')
            parts = [p.strip() for p in text.split('|')]
            tweet_num, tweet_delta, tm = int(parts[0]), int(parts[1]),float(parts[2])
        except:
            log_sys_err('Could not read %s' % ACTIVITY_FILE) 
        return tweet_num, tweet_delta, tm  
        
    @staticmethod    
    def write_activity(tweet_num, tweet_delta, tm):
        parts = tweet_num, tweet_delta, tm
        text = ' | '.join([str(p) for p in parts])        
        try:
            file(ACTIVITY_FILE, 'wt').write(text)
        except:
            log_sys_err(' Could not save activity')     
        
    def __init__(self, api):
        self._api = api
        self._last_reply_num, self._reply_delta, self._last_time = Activity.read_activity()
        Activity.write_activity(self._last_reply_num, self._reply_delta, self._last_time)
        logging.info('Activity.__init__: %s' % self)

    def __repr__(self):
        return Activity.encode_summary(self._reply_delta, self._last_time)
  
    def post_summary_tweet(self, replied_tweets, tweet):
        """Post a summary tweet from time to time.
           
        """
        tweet_num = len(replied_tweets)
   
        # To keep this infrequent, we don't post until we have 
        # exceeded the number of tweets in the last summary post
        if tweet_num <= self._last_reply_num + self._reply_delta:
            return

        summary = Activity.encode_summary(tweet_num - self._last_reply_num, self._last_time)
        print 'summary="%s" %d' % (summary, len(summary))
        logging.info('summary="%s" %d' % (summary, len(summary)))
        
        try:
            self._api.PostUpdate(summary)
            time.sleep(1)
        except Exception:
            log_sys_err(' Twitter api error posting summary "%s"' % summary)
        
        # Increase the delta each time we make a summary post
        tweet_delta = self._reply_delta + 10 
        
        parts = tweet_num, tweet_delta, tm
        self._last_reply_num, self._reply_delta, self._last_time = tweet_num, tweet_delta, tweet._time
        Activity.write_activity(tweet_num, tweet_delta, tm) 

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
            responded_user = next((u for u in l_replied_users if A(u).lower() in l_message), None)    
            if responded_user:
                logging.info('  skipping: mention: %s:"%s:' % (A(responded_user), tweet._message))
                continue
           
            reply_message = '%s Yes, paper cuts sure do hurt. I hope it gets better soon.' % A(tweet._user)             

            print '  Posting in reply to %s: %s' % (A(tweet._user), str(reply_message))
            logging.info('  Posting in reply to %s: %s' % (A(tweet._user), str(reply_message)))

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
    main_loop(55 * 60, True)
    
    