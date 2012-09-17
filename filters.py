import  re

# This list is used to exclude whole tweets that have already been seen
# It is NOT used to exclude phrases like 'Sandpaper kisses, paper cut bliss'
# These strings should be added t screen new tweets as well
# Also
#   RT
EXCLUDED_WORDS_TRAINING = [
    r'Papercut_Dolls',  # @ is treated as a word boundary
    'only creatures on earth that will cut down trees',
    'glorious\s+revenge',
    #'Paper cut. I don\'t like it lmao',
    r'holy cow balls Harry',
    r'receiving a papercut whilst signing his',
    r'The Gym Leader used a full restore.',
    r'Linkin\w*',
    r'Paper\s*cut\s*Mag\w*',
    r'Paper\s*cut\s*chron\w*',
    r'sand\s*paper\s+kisses',
    r'glorious\s+moment\s+of'
]

REPLYING_EXCLUSIONS = [
    'only creatures on earth that will cut down trees',
    'one final moment of glorious revenge',
    'Paper cut. I don\'t like it lmao',
    'holy cow balls Harry',
    'receiving a papercut whilst signing his',
    'The Gym Leader used a full restore.',
    
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
    '@papercut',
    'imagine',
    'penis',
    'vagina',
    'YouTube',
    'life gives you lemons',
    '#moneyproblems',
    'amputat',
] 

EXCLUDED_WORDS = [
    'Sandpaper\s+kisses',
    'Linkin',
    'linkin\s*park',
    'glorious',
    'revenge',   
    'cruciatus'
    'Papercut_Dolls',
    'birth',
    '@papercut',
    'papercut\s+magazine',
    'niggers?', 
    'niggas?',
    'cunts?',
    'clits?',
    'rape[sd]?',
    'deaths?',
    'eye[ -]*balls?',
    'imagine',
    'penis',
    'vaginas?',
    'YouTube',
    '#moneyproblems',
    '#np'
]

L_EXCLUDED_WORDS_TRAINING = set([e.lower() for e in EXCLUDED_WORDS_TRAINING])
L_REPLYING_EXCLUSIONS = set([e.lower() for e in REPLYING_EXCLUSIONS])
L_EXCLUDED_WORDS = set([e.lower() for e in EXCLUDED_WORDS])
L_REPLYING_EXCLUSIONS -= L_EXCLUDED_WORDS
RE_EXCLUDED_WORDS_TRAINING = re.compile(r'\b(%s)\b' % '|'.join(sorted(L_EXCLUDED_WORDS_TRAINING)))

RE_RT = re.compile(r'\brt(:|\b)')
RE_LOL = re.compile(r'\blols?\b')
RE_EYE = re.compile(r'my\s+eye')  # I think I have a paper cut I my eye.
RE_CUT = re.compile(r'cut\s*(out|back|art)\b')
RE_EXCLUDED_WORDS = re.compile(r'\b(%s)\b' % '|'.join(sorted(L_EXCLUDED_WORDS)))

RE_PAPERCUT = re.compile(r'\b#?paper\s*cuts?\b', re.IGNORECASE)

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
    return not RE_RT.search(l_message) \
       and not RE_EXCLUDED_WORDS_TRAINING.search(l_message)  
  
def is_allowed_for_replying(message): 
    if not is_allowed_for_training(message):
        return False
    l_message = message.lower().strip()
    return not any(e in l_message for e in L_REPLYING_EXCLUSIONS) \
        and not RE_LOL.search(l_message) \
        and not RE_EYE.search(l_message) \
        and not RE_CUT.search(l_message) \
        and not RE_EXCLUDED_WORDS.search(l_message) \
        and message[0] != '"' \
        and message[0] != '@'    

if __name__ == '__main__':
       
    # Print out the variables used for exclusion
    for k in sorted(globals()):
        v = globals()[k]
        if k[:2] == 'L_':
            print '%21s : %s' % (k, sorted(v))
        elif k[:3] == 'RE_':
            print '%21s : %s' % (k, v.pattern)
            
    # Run some tests  
    tests_1 = ['paper cut on my eyeball',
               'paper cut on my eyeballs',
               'paper cut on my eye-balls']
    for message in tests_1:
        print '%6s : %s' % (is_allowed_for_replying(message), message)
    
    tests_2 = ['rt message', 'log rt:message', 
        'lol rt: message', 'rt: message', 'rt hi',
        'dirt', 'rtere']
    for message in tests_2:
        print '%6s : %s' % (RE_RT.search(message) is None, message)
    
    tests_3 = ['lol papercut', 'hi lol x', 'hollow']  
    for message in tests_3:
        print '%6s : %s' % (RE_LOL.search(message) is None, message)
        

    message = '@Papercut_Dolls yes. Not exactly a promotion'.lower() 
    print message
    print is_allowed_for_training(message)
    print RE_PAPERCUT.search(message)
    print RE_RT.search(message)
    print RE_EXCLUDED_WORDS_TRAINING.search(message)  
