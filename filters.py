import  re

# This list is used to exclude whole tweets that have already been seen
# It is NOT used to exclude phrases like 'Sandpaper kisses, paper cut bliss'
# These strings should be added t screen new tweets as well
# Also
#   RT
TRAINING_EXCLUSIONS = [
    #'only creatures on earth that will cut down trees',
    #'one final moment of glorious revenge',
    #'Paper cut. I don\'t like it lmao',
    #'holy cow balls Harry',
    #'receiving a papercut whilst signing his',
    #'The Gym Leader used a full restore.',
    #'Linkin',
]

REPLYING_EXCLUSION = [
    'only creatures on earth that will cut down trees',
    'one final moment of glorious revenge',
    'Paper cut. I don\'t like it lmao',
    'holy cow balls Harry',
    'receiving a papercut whilst signing his',
    'The Gym Leader used a full restore.',
    'Linkin',
    'LOL'       # To be safe 
    'Sandpaper kisses',
    'paper cut bliss',
    'papercut bliss',
    'Bleeds to death',
    'Robin van Persie',
    #'hand sanitizer',
    'glorious',
    'revenge',   
    'cruciatus'
    'Papercut_Dolls',
    'Papercut Magazine',
    'birth',
    '@papercut',
    'nigger', 
    'nigga',
    ' cunt',
    ' clit',
    ' pape',
    'death',
    'eyeball',
    'imagine',
    ' penis',
    'vagina',
    'YouTube',
    'life gives you lemons',
    '#moneyproblems',
    'amputat',
    '#np '
] 

L_TRAINING_EXCLUSIONS = set([e.lower() for e in TRAINING_EXCLUSIONS])
L_REPLYING_EXCLUSION = set([e.lower() for e in REPLYING_EXCLUSION])

RE_RT = re.compile(r'\brt(:|\b)')
RE_LOL = re.compile(r'\blols?\b')
RE_EYE = re.compile(r'my\s+eye')  # I think I have a paper cut I my eye.
RE_CUT = re.compile(r'cut\s*(out|back|art)\b')

RE_PAPERCUT = re.compile(r'\b#?paper\s*cuts?\b', re.IGNORECASE)

if False:
    tests = ['rt message', 'log rt:message', 
        'lol rt: message', 'rt: message', 'rt hi',
        'dirt', 'rtere']
    for t in tests:
        print t, RE_RT.search(t) is not None
    tests = ['lol papercut', 'hi lol x', 'hollow']  
    for t in tests:
        print t, RE_LOL.search(t) is not None  
    exit()


RE_BAD_CHARS = re.compile(r'[\n\r\t|]')
def clean_text(message):
    """Process message so that it can be stored as
        lines of | separated fields
    """
    return RE_BAD_CHARS.sub(' ', message)

def encode_tweet_line(id, tm, user, message):
    """Encoding used for tweets in all our text files"""
    return '%s | %s | %-20s | %s' % (id, tm, user, clean_text(message))

def decode_tweet_line(line):
    line = line.rstrip('\n').strip()
    id,tm,user,message = [pt.strip() for pt in line.split('|')]
    return id,tm,user,clean_text(message)
    
def is_papercut(message):
    """Return True if message contains a variant of 'paper cut'"""
    return RE_PAPERCUT.search(message) is not None
    
def is_allowed_for_training(message):
    l_message = message.lower()
    if not RE_PAPERCUT.search(message):
        return False
    return not any(e in l_message for e in L_TRAINING_EXCLUSIONS) \
        and not RE_RT.search(l_message)

def is_allowed_for_replying(message): 
    if not is_allowed_for_training(message):
        return False
    l_message = message.lower().strip()
    return not any(e in l_message for e in L_REPLYING_EXCLUSION) \
        and not RE_LOL.search(l_message) \
        and not RE_EYE.search(l_message) \
        and not RE_CUT.search(l_message) \
        and message[0] != '"' \
        and message[0] != '@'    


