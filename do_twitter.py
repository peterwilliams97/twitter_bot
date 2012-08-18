import twitter, os, time, sys, re
from common import *
"""
    Uses 
    http://code.google.com/p/python-twitter/
"""

# Get all the file names LATEST_FILE
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

# Get access to Twitter APIs        
api = twitter.Api(**credentials)
   
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
    tm0 = time.strptime(statusObj.created_at[:-6], '%a, %d %b %Y %H:%M:%S')
    tm = time.mktime(tm0)
    user = statusObj.user.screen_name
    message = statusObj.text.encode('ascii', 'replace')
    id = statusObj.id
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
  
while True:
    # perform the search
    # until no matching tweets are found
    latest_tweet_id += 1
    results = api.GetSearch('paper cut', since_id = latest_tweet_id)
    print 'Found %s results.' % (len(results))
    if len(results) == 0:
        logging.info(' done')
        print 'Nothing to reply to. Quitting.'
        exit()

    num_relevant = 0    
    # Store the tweets in TWEETS_FILE
    fp = open(TWEETS_FILE, 'at')
    if not fp:
        logging.error('Could not open %s' % TWEETS_FILE)
    assert fp, 'Could not open %s' % TWEETS_FILE
    for i,r in enumerate(results):
        id, tm, user, message = decode_result(r)
        if is_relevant(message):
            print '%s,%s,%s,"%s"' % (id, tm, user, message)
            fp.write('%s | %s | %-20s | %s\n' % (id, tm, user, clean(message)))
            num_relevant += 1
    fp.close()
    
    latest_tweet_id = max([x.id for x in results])  

    file(LATEST_FILE, 'wt').write(str(latest_tweet_id))
    logging.info(' Added %3d relevant of %3d results, latest_id=%d' % (
             num_relevant, len(results), latest_tweet_id))
    time.sleep(10)
   
