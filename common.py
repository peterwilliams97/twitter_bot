# You will need to 
#   - write your own credentials file
#   - replace MY_TWITTER_NAME with your Twitter name
#   - replace APP_NAME with your Twitter app's name
 
CREDENTIALS_FILE = 'credentials'
MY_TWITTER_NAME = 'OwwwPapercut'
APP_NAME = 'owww_papertcut'

# The rest of the file names are derived
# from the strings above

TWITTER_ME = '@%s' % MY_TWITTER_NAME

TWEETS_FILE = '%s.tweets' % APP_NAME
LATEST_FILE = '%s.latest' % APP_NAME

CLASS_FILE = '%s.cls' % APP_NAME
LATEST_CLASS_FILE = '%s.cls_latest' % APP_NAME
NGRAM_FILE = '%s.ngram' % APP_NAME
VALIDATION_FILE = '%s.validation' % APP_NAME
MODEL_FILE = '%s.model' % APP_NAME 

REPLIES_FILE = '%s.replies' % APP_NAME

LOG_FILE = '%s.log' % APP_NAME

UNKNOWN = -1

def _clean(message):
    """Process message so that it can be stored as
        lines of | separated fields
    """
    message = message.replace('\n', ' ')
    message = message.replace('\r', ' ')
    message = message.replace('\t', ' ')
    message = message.replace('|', ' ')
    return message
 
def encode_tweet_line(id, tm, user, message):
    return '%s | %s | %-20s | %s' % (id, tm, user, _clean(message))
   
def decode_tweet_line(line):
    line = line.rstrip('\n').strip()
    id,tm,user,message = [pt.strip() for pt in line.split('|')]
    return id,tm,user,message



