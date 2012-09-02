A Twitter Bot to Offer Sympathy to Paper Cut Sufferers
======================================================

This is an exercise in writing a [Twitter-bot](http://twitter.com/OwwwPapercut). 
I am attempting to find out if it is possible
to determine with sufficient accuracy from the text of a tweet if the tweeter has suffered a 
paper cut to be able to confidentally reply with a sympathetic message.

If that is possible then I may be able to write some useful twitter bots.

How it Works
------------
The are 3 main programs

* [do_twitter.py](https://github.com/peterwilliams97/twitter_bot/blob/master/do_twitter.py) Monitors and replies to tweets on Twitter 
* [do_label.py](https://github.com/peterwilliams97/twitter_bot/blob/master/do_label.py) Used to labels tweets as indicating tweeter has a papercut 
* [do_classify.py](https://github.com/peterwilliams97/twitter_bot/blob/master/do_classify.py) Builds a tweet classification model from labelled tweets and evaluates it.  

After [installing](https://github.com/peterwilliams97/twitter_bot/blob/master/INSTALL.md) this code you can build a working twitter-bot by 
* running do_twitter.py in non-replying mode to build a corpus of tweets containing variants of the term "paper cut".
* using do_label.py to label the tweets as being from people with paper cuts or not.
* running do_classify on the corpus of labelled tweets to build a classification model.

When you have a classification model that meets your acccuracy requires you can run do_twitter.py in replying mode and see how well it chooses
which tweets to reply to. 

The following explains each of these steps in more detail.

do_twitter.py
-------------
[do_twitter.py](http://github.com/peterwilliams97/twitter_bot/blob/master/do_twitter.py) monitors and replies to tweets on Twitter.

Monitoring comprises
    Making Twitter queries to find all tweets variants of the term "paper cut".
    Doing some extra filtering on the query results.
    Saving the tweets to file.
    
Replying is somewhat more involved
    Care is taken to avoid replying more than once to a person or a conversation.
    Tweets are checked against the classification model
    Replies are made and saved to file.
    Summary tweets are generated on regular intervals so that the twitter-bot's activity can be checked by following it on Twitter.
 
do_label.py
----------- 
[do_label.py](https://github.com/peterwilliams97/twitter_bot/blob/master/do_label.py) is used to label tweets as indicating tweeter has a papercut.
It creates a text file of tweets where each line has a placehold for classification and the text of the tweet.     
e.g.

    ? | If I see one more back to school commercial I'm giving my eyes a paper cut.
    ? | i got lemon on my finger and it stings .-. stupid paper cut -.-

You should edit this file and replce the ? with the correct classfication.  
e.g.    

    n | If I see one more back to school commercial I'm giving my eyes a paper cut.
    y | i got lemon on my finger and it stings .-. stupid paper cut -.-    


