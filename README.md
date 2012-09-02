A Twitter Bot to Offer Sympathy to Paper Cut Sufferers
======================================================

This is an exercise in writing a Twitter-bot. I am attempting to find out if it is possible
to determine with sufficient accuracy from the text of a tweet if the tweeter has suffered a 
paper cut to be able to confidentally reply with a sympathetic message.

If that is possible then I may be able to write some useful twitter bots.

How it Works
------------
The are 3 main programs

* [do_twitter.py](https://github.com/peterwilliams97/twitter_bot/blob/master/do_twitter.py) Monitors and replies to tweets on Twitter 
* [do_label.py](https://github.com/peterwilliams97/twitter_bot/blob/master/do_label.py) Used to labels tweets as indicating tweeter has a papercut 
* [do_classify.py](https://github.com/peterwilliams97/twitter_bot/blob/master/[do_classify.py) Builds  tweet classification model from labelled tweets and evaluates it.  

