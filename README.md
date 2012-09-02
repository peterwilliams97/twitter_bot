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

do_classify.py
--------------    
[do_classify.py](https://github.com/peterwilliams97/twitter_bot/blob/master/do_classify.py) builds a tweet classification model from the labelled tweets 
and evaluates it.

Options:
    -n, --ngrams          show ngrams
    -s, --self-validate   do self-validation
    -c, --cross-validate  do full cross-validation
    -e, --show-errors     show false positives and false negatives
    -t <string>,          show details of how <string> was classified  
    -o, --optimize        find optimum threshold, back-offs and smoothings
    -m, --model           save calibration model
    
You should run do_classify.py -c to see how well the classification predicts new tweets based on 
[cross-validation](http://en.wikipedia.org/wiki/Cross-validation_\(statistics\))

It will produce some output like this

    ===== = ===== = =====
          | False |  True
    ----- + ----- + -----
    False |  1876 |   165
    ----- + ----- + -----
     True |   189 |   995
    ===== = ===== = =====
    Total = 3225

    ===== = ===== = =====
          | False |  True
    ----- + ----- + -----
    False |   58% |    5%
    ----- + ----- + -----
     True |    5% |   30%
    ===== = ===== = =====
    Precision = 0.858, Recall = 0.840, F1 = 0.849 

The columns are the predicted classifications of the tweets and rows ares the actual classifications.

In this result 3225 tweets were evaluated and
* 1876 were _correctly_ predicted as people tweeting about their paper cuts.   
* 995 were _correctly_ predicted as __not__ people tweeting about their paper cuts. 
* 165 were _incorrectly_ predicted as people tweeting about their paper cuts.   
* 189 were incorrectly predicted as __not__ people tweeting about their paper cuts. 

[F1](http://en.wikipedia.org/wiki/F1_score) is a score between 0 and 1 that we want to be as close to 1 as possible. 

In this example an F1 of 0.85 is reasonable but not great. The 
[precision](http://en.wikipedia.org/wiki/Precision_\(information_retrieval\))
of 0.86 means that 86% of the tweets predicted to be people tweeting about the paper cuts are so, and therefore that 14% are not.
This is important. It means that 14% of the replies we make could be wrong. We calls these 
[false positives](http://en.wikipedia.org/wiki/Type_I_and_type_II_errors#False_positive_error).

We therefore run `do_classify.py -e` to see what these false positives are.

      27    0.95: #ItHurts when I get a paper cut. :/ Those little cuts KILL!
     2115   0.98: @crimescript Sounds pretty nasty. The worst, medically, I face in my job is a paper cut :o) But then my job is dull &amp; not good book material
     2116   0.99: ....and paper cut ????????
      764   1.03: Why is the first day of work after vacation have to be like giving yourself a papercut then pouring vodka in it? #retailproblems
     2950   1.06: Lol only you would mysteriously pop up with a paper cut. 

27, 2116 amd 764 seem ambiguous and could be mistaken as being tweets from people with paper cuts. The other two are definitely not. 
Another filter we use (tweets starting with @) will reomove 2115. 

Based on this analysis of 5 tweets the twitter-bot's replies may not be too inappropriate. (Using 5 tweets was for illustration
only. In a real analysis we would evaluate all 165 false positive tweets.)

When our classification model is peforming well enough we run `do_classify.py -m` to save it.

At this stage we run `do_twitter.py 30 -r` and see how the twitter-bot performs 
[interacting with people](http://twitter.com/OwwwPapercut/favorites) on twitter.

  