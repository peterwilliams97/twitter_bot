"""
    We classify tweets as one of 
       True : We should reply to the tweet
       False: We should not reply to the tweets
       UNKNOWN: We don't know
       
    In all our text files we encode True/False/Unknown as 
        True: 'y',  
        False: 'n',
        UNKNOWN: anything other than 'y' or 'n'. Some values we use are 
            '?': Means we don't know
            'Y': Means we (or a program) guessed True
            'N': Means we (or a program) guessed False

    This module is for labelling tweets so that we can use the 
    labelled tweets for training a classifier.

""" 

UNKNOWN = -1

CLASS_LABELS = {
    True: 'y',  
    False: 'n',
    UNKNOWN: '?'
}
LABELS_CLASSES = dict([(v,k) for k,v in CLASS_LABELS.items()])

AUTO_CLASSES_LABELS = {
    False: 'N',
    True: 'Y',  
    UNKNOWN: '?'
}  

def get_class(label):
    """Return class matching label"""
    return LABELS_CLASSES.get(label, UNKNOWN)

