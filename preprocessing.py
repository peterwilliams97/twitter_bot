from __future__ import division
"""
    Preprocessing functions common to all our classifiers.
"""
import re

# Text between quotation marks.
RE_QUOTE = re.compile(r'''(?:'(?!\S)|(?<!\S)'|")''')

# In Twitter 'some text @someone: some quote' is a way of quoting 'some quote'
# You really are living the life. ?@sockin_bxxches: just got a paper cut from counting money...no boost?
RE_QUOTE2 = re.compile(r'@\w+\s*:.+$')
RE_QUOTE3 = re.compile(r'\brt\b.+$')

def _remove_quoted_text(message):
    """Remove quoted text from message because it we presume it was 
        not written the author of message
    """

    message = RE_QUOTE2.sub(' ', message)

    message = RE_QUOTE3.sub(' ', message)    

    # Split message by ' and "
    parts = RE_QUOTE.split(message)

    # in_quote is true between quote marks
    # discard these parts
    in_quote = False
    out_parts = []
    for p in parts:
        out_parts.append(' ' if in_quote else p)
        in_quote = not in_quote
    message = ' '.join(out_parts) 
        
    return message    

RE_PAPERCUT = re.compile(r'\b#?paper\s*cuts?\b')
    
RE_USER = re.compile(r'@+\w+')
RE_HTTP = re.compile(r'http://\S+')

RE_SYM = re.compile(r'&(\w+);')
RE_SYM2 = re.compile(r'(\[TAG_SYMBOL\])\1\1*')

RE_AMP = re.compile(r'&amp;')
RE_GT = re.compile(r'&gt;')
RE_LT = re.compile(r'&lt;')
RE_PUNC = re.compile(r'[,.;:-]')
RE_PUNC2 = re.compile(r'[!?\']{2,}')
RE_PUNC3 = re.compile(r'\?')
RE_PUNC4 = re.compile(r'\?[\s\?]+')
RE_BRACKETS = re.compile(r'[\(\)\{\}]+')
RE_SPACE = re.compile(r'\s+')
RE_HASH = re.compile(r'#(\w+)')
RE_REPEAT = re.compile(r'(.)\1\1+')
RE_REPEAT2 = re.compile(r'[<>](\s*[<>])+')

RE_BANG = re.compile(r'(\w+)([!])')
RE_NUMBER = re.compile(r'\d+(\s+\d)*')
RE_JUNK = re.compile(r'[@*#%+=&/\^\$]+')

def pre_tokenize(message):
    """The preprocessing performed on text before tokenization
    """
    
    # This is for a "paper cut" classifier so text must contain "paper cut" 
    assert RE_PAPERCUT.search(message), message
    
    message = _remove_quoted_text(message)
    
    message = RE_USER.sub('[TAG_USER]', message)
    message = RE_HTTP.sub(' [TAG_LINK] ', message)
    
    message = RE_PAPERCUT.sub(' PAPER_CUT ', message)
    
    message = RE_AMP.sub(' & ', message)
    message = RE_GT.sub(' < ', message)
    message = RE_LT.sub(' > ', message)
    message = RE_SYM.sub(r' \1 ', message) 
    message = RE_SYM.sub(r' [TAG_SYMBOL] ', message) 
    message = RE_SYM2.sub(r' [TAG_SYMBOL] ', message) 
       
    message = RE_PUNC.sub(' ', message)
    message = RE_PUNC2.sub(' ! ', message)
    message = RE_PUNC3.sub(r' ? ', message)
    message = RE_PUNC4.sub(r' ? ', message)
    message = RE_BRACKETS.sub(' ', message)
    
    message = RE_SPACE.sub(' ', message)
    
    message = RE_HASH.sub(r'\1', message)
        
    message = RE_REPEAT.sub(r'\1', message) 
    #message = RE_REPEAT.sub(r'\1\1', message)
    message = RE_REPEAT2.sub(r'>', message) 
    
    message = RE_BANG.sub(r'\1 \2', message)
    
    message = RE_JUNK.sub(r' [TAG_JUNK] ', message) 
  
    message = RE_NUMBER.sub(' [TAG_NUMBER] ', message)
        
    return message
  
# The stop words that have been tried and found to be ineffective are
#  left in the code and commented out'
# I was surprised at how many common words improved classification for 
#  this classifier of tweets as being from people with papercuts or not.  
STOP_WORDS = set([
    'the',
    'and',
    'that', 
    #'or',
    #'did',
    #'it',
    #'is',
    #'get',
    #'got',
    #'a',       # Excluding 'a' increases precision and decreases recall
    #'have', 
    #'my',
    #'i',
    #'of'
    # 'in', 'on', 'at'
    ])    
 
def post_tokenize(words):
    """Post-process list of words created from tokenization
        Remove stop words
        Remove words after indicators that they are not meant
    """
    words = [w for w in words if w not in STOP_WORDS]
    
    out_words = []
    skip_from = -1
    for i,w in enumerate(words):
        if skip_from >= 0:
            if i <= skip_from + 2:
                continue
            else:
                skip_from = -1
        if w in set(['almost', 'she', 'he', 'except', 'like', 'not', "ain't", 
                    'who']):
            skip_from = i
            continue
        out_words.append(w)    
    
    out_words = ['[TAG_START]'] + out_words +  ['[TAG_END]'] 
    return out_words      

# We store ngrams as WORD_DELIMITER separated strings internally as
#  Python's string processing is fast. 
# Use the following functions to split ngrams into words and join 
#  words into ngrams.
#    
WORD_DELIMITER = ' '    

def get_bigrams(words):    
    """Return all the bigrams in the list of words"""
    return [WORD_DELIMITER.join(words[i-1:i+1]) for i in range(1,len(words))]

def get_trigrams(words):    
    """Return all the trigrams in the list of words"""
    return [WORD_DELIMITER.join(words[i-2:i+1]) for i in range(2,len(words))]
    
def get_ngrams(n, words):    
    """Return all the ngrams in the list of words"""
    if n == 1:
        words = [w for w in words if w != 'PAPER_CUT']
        return words[1:-1] # Trim the [TAG_START] and [TAG_END]
    return [WORD_DELIMITER.join(words[i:i+n]) for i in range(len(words)-n)]    
    
import PorterStemmer    
stemmer = PorterStemmer.PorterStemmer()    

def extract_words(message, do_stem = False):
    """The word extractor that is run over every message that is trained on or
        classified or None if 'paper cut' was removed in processing.
    """
    message = message.lower()
    
    if do_stem:
        message2 = stemmer.stem(message)

    message = pre_tokenize(message)

    words = message.split()

    words = post_tokenize(words) 

    return words if ('PAPER_CUT' in words) else None
