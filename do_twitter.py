"""
    Program to monitor Twitter for people tweeting about their paper cuts
     and optionally reply to them.
     
    Uses http://code.google.com/p/python-twitter/
"""
import twitter, os, time, sys, re

# Our shared modules
import common, filters

import logging
logging.basicConfig(filename = common.LOG_FILE, 
            level = logging.INFO,
            format = '%(asctime)s %(message)s')

def log_sys_err(msg):
    """Log serious errors with system exceptions"""
    full_msg = '%s : %s' % (msg, str([sys.exc_info()[:2]]))
    print full_msg
    logging.error(full_msg)
    time.sleep(1)

def A(user):
    return '@%s' % user
  
def get_reply_message(user):
    """Our reply to people who have tweeted about their paper cuts"""
    return '@%s Yes, paper cuts sure do hurt. I hope it gets better soon.' % user 

def is_relevant(twitter_status):
    """We are looking for tweets that contain 'papercut'"""
    message = filters.clean_text(twitter_status.text.encode('ascii', 'replace'))
    return filters.is_papercut(message)

"""
    We want a date/time format like
        9:14pm for today
        5:02pm Wed 29 Aug for past days
"""
from datetime import datetime
LOCAL_TIME_DELTA = datetime.now() - datetime.utcnow()
LOCAL_TIME_DELTA
SUMMARY_DAY_FORMAT = '%I:%M%p' 
SUMMARY_TM_FORMAT = '%I:%M%p %a %d %b' 
RE_TIME = re.compile(r'(\d+):(\d+)(AM|PM)', re.IGNORECASE)

def _same_day(dt1, dt2):
    return  dt1.year == dt2.year and dt1.month == dt2.month and dt1.day == dt2.day

def _time_replacer(m):
    hr,min,ap = m.groups()
    return '%d:%02d%s' % (int(hr),int(min),ap.lower())
        
def get_local_time_str(tm):
    gmt = datetime(*time.localtime(tm)[:6])
    gmt += LOCAL_TIME_DELTA
    format = SUMMARY_DAY_FORMAT if _same_day(gmt, datetime.now()) else SUMMARY_TM_FORMAT
    return RE_TIME.sub(_time_replacer, gmt.strftime(format))
 
class ScoredTweet:
    """A ScoredTweet contains information about a tweet and a score for that
        tweet
        
        Tweet info:
            _id: unique id of tweet
            _time: time of tweet
            _user: user name of tweeter
            _message: text of tweet
        Score:        
            _replyable : True if we are really sure the tweeter had a
                paper cut
            _score: log(odds ratio) of tweet being positive 
    """
    def __init__(self, model, twitter_status):
        # Decode the twitter_status
        tm0 = time.strptime(twitter_status.created_at[:-6], '%a, %d %b %Y %H:%M:%S')
        self._time = time.mktime(tm0)
        self._user = twitter_status._user.screen_name
        self._message = filters.clean_text(twitter_status.text.encode('ascii', 'replace'))
        self._id = twitter_status._id
        
        # Score the decoded status
        if model:
            positive, self._score =  model.classify(self._message)
        else: 
            positive, self._score = False, 0.0
        self._replyable = positive and filters.is_allowed_for_replying(self._message) 

    def __repr__(self):
        return '%-5s|%6.2f|%s"' % (self._replyable, self._score, self.get_tweet_line())  

    def get_tweet_line(self):
        return filters.encode_tweet_line(self._id, self._time, self._user, self._message)

    def get_scored_line(self): 
        return ' %-5s %6.2f %-15s : "%s"' % (self._replyable, self._score, A(self._user), self._message)  

def load_replied_tweets():
    """Returns a list of (id,user) of the tweets already replied to
    """
    
    replied_tweets = []

    try:
        fp = open( common.REPLIES_FILE, 'rt')
    except IOError:    
        logging.error('Could not open %s',  common.REPLIES_FILE)
        return replied_tweets

    try:    
        for line in fp:
            line = line.rstrip('\n').strip()
            if line:
                id,_,user,_ = filters.decode_tweet_line(line)
                replied_tweets.append((id, user))
    finally:
        fp.close()    
    
    return replied_tweets    
    
def get_replied_users(replied_tweets):
    """Given the list of tweets replied to,
        returns the set of users replied to in lower case
    """ 
    return set(user.lower() for _,user in replied_tweets)

def fetch_latest_scored_tweets(api, model, latest_tweet_id): 
    """Fetch some tweets containing 'paper cut' from
        Twitter and return them as a list of ScoredTweets
    """    

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
    """Store the ScoredTweets in scored_tweets in  common.TWEETS_FILE
    """
 
    try:
        fp = open( common.TWEETS_FILE, 'at')
    except:     
        logging.error('Could not open %s' %  common.TWEETS_FILE)
        return

    try:    
        for tweet in scored_tweets:
            logging.info(tweet.get_scored_line())
            fp.write('%s\n' % tweet.get_tweet_line())
    finally:
        fp.close()

class Activity:
    """An activity record.
        This is used for generating summary tweets based on our tweet reply 
        activity
    
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
            text = file( common.ACTIVITY_FILE, 'rt').read().strip('\n')
            parts = [p.strip() for p in text.split('|')]
            tweet_num, tweet_delta, tm = int(parts[0]), int(parts[1]),float(parts[2])
        except:
            log_sys_err('Could not read %s' %  common.ACTIVITY_FILE) 
        return tweet_num, tweet_delta, tm  

    @staticmethod    
    def write_activity(tweet_num, tweet_delta, tm):
        parts = tweet_num, tweet_delta, tm
        text = ' | '.join([str(p) for p in parts])        
        try:
            file(common.ACTIVITY_FILE, 'wt').write(text)
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
        logging.info('summary="%s" %d' % (summary, len(summary)))
        
        try:
            self._api.PostUpdate(summary)
            time.sleep(1)
        except Exception:
            log_sys_err(' Twitter api error posting summary "%s"' % summary)
        
        # Increase the delta each time we make a summary post
        tweet_delta = self._reply_delta + 10 

        self._last_reply_num, self._reply_delta, self._last_time = tweet_num, tweet_delta, tweet._time
        Activity.write_activity(tweet_num, tweet_delta, tweet._time) 

FRIENDLIES = [
    'peter_c_william',
    'alecthegeek',
    'PaperCutDev'
]
l_friendly_users = set(user.lower() for user in FRIENDLIES)
        
def reply_to_tweets(api, activity, replied_tweets, scored_tweets):
    """Make Twitter replies to scored_tweets
        api: Twitter API object
        activity: An Activity record
        replied_tweets: List of all tweets that we have ever replied to
        scored_tweets: List of recently tweets that are candidates for replying to/
    """

    l_replied_users = get_replied_users(replied_tweets)

    try:
        fp = open(common.REPLIES_FILE, 'at')
    except IOError:    
        # We MUST bail out here as we risk replying to tweets more than once
        # if we don't record who we have replied to.
        logging.error('Could not open %s', common.REPLIES_FILE)
        return

    try:    
        for tweet in scored_tweets:
            l_message = tweet._message.lower()
      
            # Don't reply to users more than once
            if tweet._user.lower() in l_replied_users:
                # unless they are friendly
                if tweet._user.lower() not in l_friendly_users:
                    logging.info(' skipping: already replied to %s' % tweet._user)
                    continue 
            # Don't reply to responses    
            if common.TWITTER_ME.lower() in l_message:
                logging.info('  skipping:  response "%s"' % tweet._message)
                continue
            # Don't reply to mentions of tweets we have responded to
            responded_user = next((u for u in l_replied_users if A(u).lower() in l_message), None)    
            if responded_user:
                logging.info('  skipping: mention: %s:"%s:' % (A(responded_user), tweet._message))
                continue
           
            reply_message = get_reply_message(tweet._user)             

            logging.info('  Posting in reply to %s: %s' % (A(tweet._user), str(reply_message)))

            # Update replied list before replying in case something goes wrong 
            # in updating list or replying
            replied_tweets.append((tweet._id, tweet._user))
            fp.write('%s\n' % tweet.get_tweet_line())
            l_replied_users.add(tweet._user.lower())

            try:
                api.PostUpdate(reply_message, in_reply_to_status_id=tweet._id)
                time.sleep(1)
            except Exception:
                logging.error(' Twitter api error: %s' % str(sys.exc_info()[0:2]))

            activity.post_summary_tweet(replied_tweets, tweet)

    finally:        
        fp.close()        

def run_main_loop(max_duration, replying_enabled): 
    """The out monitor/reply loop for communicating with Twitter
        max_duration: Maximum time to run this loop for (seconds)
        replying_enabled: Reply to tweets?
    """    

    logging.info('max_duration=%d, replying_enabled=%s' % (max_duration, replying_enabled))
    start_time = time.time()
    # Delay between loops
    delay = 0.1
    
    def elapsed(): 
        """Elapsed time since start"""
        return time.time() - start_time
        
    # Load the classification model first
    # This is critical for classifying tweets for reply
    # It is helpful for seeing which tweets would be replied to 
    #  when we are running in non-replying mode
    # The model will not be available in early stage of development
    #  before tweets have been saved and labeled
    model = common.load_model() 
    if replying_enabled:
        assert model, 'Cannot reply with a classification model'
    
    # Lastest tweet id (an integer) is stored as text in LATEST_FILE
    # We use to prevent re-reading tweets
    latest_tweet_id = int(file(common.LATEST_FILE, 'rt').read().strip()) if os.path.exists(common.LATEST_FILE) else 0
    logging.info('latest_tweet_id=%d' % latest_tweet_id)
    
    # Load the tweets that have already been replied to
    replied_tweets = load_replied_tweets()

    # Credentials are stored in CREDENTIALS_FILE as text lines of key='value' 
    # The keys are: consumer_key, consumer_secret, access_token_key, access_token_secret 
    RE_CREDENTIALS = re.compile(r"(\w+)='([^']+)'")
    credentials = dict((m.group(1),m.group(2)) 
        for m in RE_CREDENTIALS.finditer(file(common.CREDENTIALS_FILE,'rt').read()))
    
    # Create an object that gives access to the Twitter APIs        
    api = twitter.Api(**credentials)
    
    # Create an Activity object for generating summary tweets
    activity = Activity(api)
    
    # The main loop. Runs for max_duration seconds with delay seconds
    #  between iterations.
    while elapsed() + delay < max_duration:
        time.sleep(delay)
        
        # Fetch tweets that were created since the last time we checked
        latest_tweet_id += 1
        scored_tweets = fetch_latest_scored_tweets(api, model, latest_tweet_id) 
        
        if scored_tweets:
            # Record all tweets
            scored_tweets.sort(key = lambda t: (not t._replyable, -t._score, t._id)) 
            latest_tweet_id = max([t._id for t in scored_tweets])
            file(common.LATEST_FILE, 'wt').write(str(latest_tweet_id))
            record_tweets(scored_tweets)

            replyable_tweets = [t for t in scored_tweets if t._replyable]
            # Reply to all the tweeets that we should reply to 
            if replying_enabled and replyable_tweets:
                reply_to_tweets(api, activity, replied_tweets, replyable_tweets)
        
        # Back off if there were no matching tweets
        delay = 10 if scored_tweets else delay * 2
        delay = max(10, min((abs(elapsed() - max_duration)/10), delay))
        
        logging.info('Found %3d replyable of %3d relevant results, latest_id=%d, sleeping %5.1f sec, running %4d sec (%4d remaining)' % (
                    len([t for t in scored_tweets if t._replyable]), 
                    len(scored_tweets), latest_tweet_id,
                    delay,  elapsed(), max_duration - elapsed()))

if __name__ == '__main__':
    """Run the main loop for a specified amount of time
        and catch all fatal exceptions.
       This progam is expected to be run by a scheduler that restarts it 
        after max_duration + 5 minutes
    """
    import optparse

    parser = optparse.OptionParser('python %prog [options] <duration(min)>')
    parser.add_option('-r', '--reply', action='store_true', dest='replying_enabled', default=False, help='reply to tweets')
    (options, args) = parser.parse_args()
    if len(args) < 1:
        parser.error('Duration not specified') 

    max_duration = int(args[0]) * 60   
       
    logging.info('-' * 80)
    logging.info('Starting %s' % str(sys.argv[0]))
    try:
        run_main_loop(max_duration, options.replying_enabled)
    except Exception:
        log_sys_err('Uncaught error')
    logging.info('Finished normally')    
    