import os, re, pickle

# You will need to 
#   - write your own credentials file
#   - replace MY_TWITTER_NAME with your Twitter name
#   - replace APP_NAME with your Twitter app's name
 
CREDENTIALS_FILE = 'credentials'
MY_TWITTER_NAME = 'OwwwPapercut'
APP_NAME = 'owww_papertcut'

DATA_DIR = './data'

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

# The last classification model we constructed
MODEL_FILE = _make_path('model') 

REPLIES_FILE = _make_path('replies')
ACTIVITY_FILE = _make_path('activity')

LOG_FILE = _make_path('log')


def save_model(model):
    """Save model to MODEL_FILE"""
    pickle.dump(model, open(MODEL_FILE, 'wb'))

def load_model():
    """Load a classification model from MODEL_FILE"""
    model = pickle.load(open(MODEL_FILE, 'rb'))
    return model





