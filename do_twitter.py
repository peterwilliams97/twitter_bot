import twitter, os, time, sys, re
from common import *

"""
    Based on ideas and code in 
    http://inventwithpython.com/blog/2012/03/25/how-to-code-a-twitter-bot-in-python-on-dreamhost/
"""

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
RE_PAPERCUT = re.compile(r'paper\s+cut')
def is_relevant(message):
    message = message.lower()
    if not RE_PAPERCUT.search(message):
        return False
    return True
    
def clean(message):
    message = message.replace('\n', ' ')
    message = message.replace('\r', ' ')
    message = message.replace('\t', ' ')
    message = message.replace('|', ' ')
    return message

if False:
    tweet_list = []    
    for statusObj in results:
        id, tm, user, message = decode_result(statusObj)
        print '%s,%s,%s,"%s"' % (id, tm, user, message)
        tweet_list.append((id, tm, user, message))    
    #tweet_list = [r for r in tweet_list if is_relevant(r[3])]    

while True:
    # perform the search
    latest_tweet_id += 1
    results = api.GetSearch('paper cut', since_id = latest_tweet_id)
    print 'Found %s results.' % (len(results))
    if len(results) == 0:
        logging.info(' done')
        print 'Nothing to reply to. Quitting.'
        exit()

    num_relevant = 0    
    # Store the tweets
    fp = open(TWEETS_FILE, 'at')
    if not fp:
        logging.error('Could not open %s' % TWEETS_FILE)
    assert fp, 'Could not open %s' % TWEETS_FILE
    for i,statusObj in enumerate(results):
        id, tm, user, message = decode_result(statusObj)
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
exit()    

#
#  DONE !!!!
#

def A(user):
    return ('@%s' % user)
    
one_day_ago = time.time() - 24*60*60
l_messaged_users = set(A(u).lower for u in alreadyMessaged) 

for statusObj in results:
    id, tm, user, message = decode_result(statusObj)
    l_message = message.lower()

    if tm > one_day_ago and A(user).lower() not in l_messaged_users and TWITTER_ME not in message:
        if any(u in l_message for u in l_messaged_users):
            #print 'Skipping because it\'s a mention: @%s - %s' % (statusObj.user.screen_name.encode('ascii', 'replace'), statusObj.text.encode('ascii', 'replace'))
            continue

        try:
            #print 'Posting in reply to @%s: %s' % (statusObj.user.screen_name.encode('ascii', 'replace'), statusObj.text.encode('ascii', 'replace'))
            api.PostUpdate('%s Yes, paper cuts hurt. Hope it gets better soon.' % user, 
                    in_reply_to_status_id=id)
            repliedTo.append( (id, user, message('ascii', 'replace')) )
            time.sleep(1)
        except Exception:
            print "Unexpected error:", sys.exc_info()[0:2]


file(LATESTFILE, 'wt').write(str(max([x.id for x in results])))

fp = open(LOGFILE, 'at')
fp.write('\n'.join(['%s|%s|%s' % (x[0], x[1], x[2]) for x in repliedTo]) + '\n')
fp.write('\n')
fp.close()