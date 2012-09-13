Data Files
==========

[owww_papertcut.tweets](https://raw.github.com/peterwilliams97/twitter_bot/master/data/owww_papertcut.tweets) 
is all the tweets recorded by do_twitter.py.

[owww_papertcut.latest](https://github.com/peterwilliams97/twitter_bot/blob/master/data/owww_papertcut.latest)
is the id of the latest tweet do_twitter.py has fetched from Twitter.

[owww_papertcut.replies](https://github.com/peterwilliams97/twitter_bot/blob/master/data/owww_papertcut.replies)
is all the tweets replied to by [OwwwPapercut](http://twitter.com/OwwwPapercut). 

[owww_papertcut.cls](https://github.com/peterwilliams97/twitter_bot/blob/master/data/owww_papertcut.cls)
is the list of hand-labelled tweets used to train 
[BayesClassifier.py](https://github.com/peterwilliams97/twitter_bot/blob/master/BayesClassifier.py).

[owww_papertcut.activity](https://raw.github.com/peterwilliams97/twitter_bot/master/data/owww_papertcut.activity) 
tracks the number of tweets over time for the Activity class in 
[do_twitter.py](https://github.com/peterwilliams97/twitter_bot/blob/master/do_twitter.py). 

[owww_papertcut.model](https://raw.github.com/peterwilliams97/twitter_bot/master/data/owww_papertcut.model)
is the pickle of the trained BayesClassifier.py used by do_twitter.py to classify tweets as being about
from people with paper cuts or not.

[owww_papertcut.ngram](https://raw.github.com/peterwilliams97/twitter_bot/master/data/owww_papertcut.ngram)
are the n-gram counts of the trained BayesClassifier.py.