# You will need to 
#   - write your own credentials file
#   - replace MY_TWITTER_NAME with your Twitter name
#   - replace APP_NAME with your Twitter app's name
 
CREDENTIALS_FILE = 'credentials'
MY_TWITTER_NAME = 'OwwwPapercut'
APP_NAME = 'owww_papertcut'

import os
DATA_DIR = './data'

try:
    os.mkdir(DATA_DIR)
except:
    pass


def _make_path(ext):
    return os.path.join(DATA_DIR, '%s.%s' % (APP_NAME, ext))


# The rest of the file names are derived
# from the strings above

TWITTER_ME = '@%s' % MY_TWITTER_NAME

TWEETS_FILE = _make_path('tweets')
LATEST_FILE = _make_path('latest')

CLASS_FILE= _make_path('cls')
LATEST_CLASS_FILE = _make_path('cls_latest')
NGRAM_FILE = _make_path('ngram')
VALIDATION_FILE = _make_path('validation')
MODEL_FILE = _make_path('model') 

REPLIES_FILE= _make_path('replies')

LOG_FILE = _make_path('log')

UNKNOWN = -1

def clean_text(message):
    """Process message so that it can be stored as
        lines of | separated fields
    """
    message = message.replace('\n', ' ')
    message = message.replace('\r', ' ')
    message = message.replace('\t', ' ')
    message = message.replace('|', ' ')
    return message
 
def encode_tweet_line(id, tm, user, message):
    return '%s | %s | %-20s | %s' % (id, tm, user, clean_text(message))
   
def decode_tweet_line(line):
    line = line.rstrip('\n').strip()
    id,tm,user,message = [pt.strip() for pt in line.split('|')]
    return id,tm,user,clean_text(message)
  



