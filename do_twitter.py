import twitter, os, time, sys, re
from common import *
"""
    Uses 
    http://code.google.com/p/python-twitter/
"""

# Get all the file names *_FILE
from common import *

import logging
logging.basicConfig(filename = LOG_FILE, 
            level = logging.INFO,
            format = '%(asctime)s %(message)s')
logging.info('Starting '+ sys.argv[0])

# Credentials are stored in CREDENTIALS_FILE as text lines of key='value' 
# The keys are: consumer_key, consumer_secret, access_token_key, access_token_secret 
RE_CREDENTIALS = re.compile(r"(\w+)='([^']+)'")
credentials = dict((m.group(1),m.group(2)) for m in RE_CREDENTIALS.finditer(file(CREDENTIALS_FILE,'rt').read()))
 
# Lastest tweet id (an integer) is stored as text in LATEST_FILE
# We use to prevent re-reading tweets
latest_tweet_id = int(file(LATEST_FILE, 'rt').read().strip()) if os.path.exists(LATEST_FILE) else 0

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
    
def clean(message):
    """Process message so that it can be stored as
        lines of | separated fields
    """
    message = message.replace('\n', ' ')
    message = message.replace('\r', ' ')
    message = message.replace('\t', ' ')
    message = message.replace('|', ' ')
    return message
  
# Get access to Twitter APIs        
api = twitter.Api(**credentials)
  
while True:
    # perform the search
    # until no matching tweets are found
    latest_tweet_id += 1
    results1 = api.GetSearch('paper cut', since_id = latest_tweet_id)
    time.sleep(2)
    results2 = api.GetSearch('papercut', since_id = latest_tweet_id)
    results = results1 + results2
    print 'Found %s results = %d + %d' % (len(results), len(results1), len(results2))
    if len(results) == 0:
        logging.info(' done')
        print 'Nothing to reply to. Quitting.'
        exit()
    tweets = [decode_result(r) for r in results]    
    tweets.sort(key = lambda t: t[0])
    id_list = [t[0] for t in tweets]
    if len(set(id_list)) != len(id_list):
        print 'Duplicate ids!'

    num_relevant = 0    
    # Store the tweets in TWEETS_FILE
    fp = open(TWEETS_FILE, 'at')
    if not fp:
        logging.error('Could not open %s' % TWEETS_FILE)
    assert fp, 'Could not open %s' % TWEETS_FILE
    for i,t in enumerate(tweets):
        id, tm, user, message = t
        if is_relevant(message):
            line = '%s | %s | %-20s | %s' % (id, tm, user, clean(message))
            print line
            fp.write('%s\n' % line)
            num_relevant += 1
    fp.close()
    
    latest_tweet_id = max([x.id for x in results])  

    file(LATEST_FILE, 'wt').write(str(latest_tweet_id))
    logging.info(' Added %3d relevant of %3d results, latest_id=%d' % (
             num_relevant, len(results), latest_tweet_id))
    time.sleep(10)
   
