A Twitter Bot to Offer Sympathy to Paper Cut Sufferers
======================================================

This is an exercise in writing a [Twitter-bot](http://twitter.com/OwwwPapercut). 
I am attempting to find out if it is possible
to determine from the text of a tweet alone if the tweeter has suffered a 
paper cut. 

The Twitter-bot also gratuitouslty ests the acccuracy of its predictions by replying to 
those tweets it has determined to be from paper cut sufferers with a 
[sympathetic message](https://github.com/peterwilliams97/twitter_bot/blob/master/do_twitter.py#L27-29).

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
    Summary tweets are generated on regular intervals so that the twitter-bot's activity can be checked with a 
    [Twitter query](http://twitter.com/#!/search/%40owwwpapercut%20liebig).
    
[OwwwPapercut](http://twitter.com/OwwwPapercut) is currently being run from an AWS Ubuntu 
micro-instance with the following crontab line.
    
    29 * * * * python /home/ubuntu/twitter_bot/do_twitter.py 55 -r
 
do_label.py
----------- 
[do_label.py](https://github.com/peterwilliams97/twitter_bot/blob/master/do_label.py) is used to label tweets as indicating tweeter 
has a papercut.  It creates a text file of tweets where each line has a placehold for classification and the text of the tweet.     
e.g.

    ? | If I see one more back to school commercial I'm giving my eyes a paper cut.
    ? | i got lemon on my finger and it stings .-. stupid paper cut -.-

You should edit this file and replce the ? with the correct classfication.  
e.g.    

    n | If I see one more back to school commercial I'm giving my eyes a paper cut.
    y | i got lemon on my finger and it stings .-. stupid paper cut -.-    

do_classify.py
--------------    
[do_classify.py](https://github.com/peterwilliams97/twitter_bot/blob/master/do_classify.py) builds a tweet classification model from 
the labelled tweets end evaluates it. The classifier is discussed later under the heading [The Classifier](#the-classifier).

Options:
    -n, --ngrams          show ngrams
    -s, --self-validate   do self-validation
    -c, --cross-validate  do full cross-validation
    -e, --show-errors     show false positives and false negatives
    -t <string>,          show details of how <string> was classified  
    -o, --optimize        find optimum threshold, back-offs and smoothings
    -m, --model           save calibration model
    
You should run `python do_classify.py -c` to see how well the classification predicts new tweets based on 
[cross-validation](http://en.wikipedia.org/wiki/Cross-validation_\(statistics\)). 

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
* 1876 were __correctly__ predicted as people tweeting about their paper cuts.   
* 995 were __correctly__ predicted as _not_ people tweeting about their paper cuts. 
* 165 were __incorrectly__ predicted as people tweeting about their paper cuts.   
* 189 were __incorrectly__ predicted as _not_ people tweeting about their paper cuts. 

(These numbers are from the start of development. Scores for the current code are 
[here](https://github.com/peterwilliams97/twitter_bot/blob/master/results/cv.latest).)

The measures _Precision_, _Recall_ and _F1_ are explained 
[here](http://tomazkovacic.com/blog/74/evaluation-metrics-for-text-extraction-algorithms/)
* Precision is the fraction of tweets predicted to be about paper cuts that actually were.
* Recall is the fraction of tweets about paper cuts that were predicted as being so.
* F1 is a combined measure that increases with increasing precision and increasing recall.

We especially want precision to be high so that we don't reply to people who don't have paper cuts.
We also want recall to be high so we can reply to as many paper cut sufferers as possible 

In this example an F1 of 0.85 is reasonable but not great. The precision of 0.86 means that 86% of the tweets 
predicted to be people tweeting about the paper cuts are so, and therefore that 14% are not.
This is important. It means that 14% of the replies we make could be wrong. We call these replies 
[false positives](http://en.wikipedia.org/wiki/Type_I_and_type_II_errors#False_positive_error).

We therefore run `python do_classify.py -e` to see what these false positives are.

      27    0.95: #ItHurts when I get a paper cut. :/ Those little cuts KILL!
     2115   0.98: @crimescript Sounds pretty nasty. The worst, medically, I face in my job is a paper cut :o) But then my job is dull &amp; not good book material
     2116   0.99: ....and paper cut ????????
      764   1.03: Why is the first day of work after vacation have to be like giving yourself a papercut then pouring vodka in it? #retailproblems
     2950   1.06: Lol only you would mysteriously pop up with a paper cut. 

27, 2116 amd 764 seem ambiguous and could be mistaken as being tweets from people with paper cuts. The other two are definitely not. 
Another filter we use (tweets starting with @) will reomove 2115. 

Based on this analysis of 5 tweets the twitter-bot's replies may not be too inappropriate. 

(Using 5 tweets was for illustration only. In a real analysis we would evaluate all 165 false positive tweets.
You can see the false positives in the current version of the classfier 
[before](https://github.com/peterwilliams97/twitter_bot/blob/master/results/false.negatives.latest) and
[after](https://github.com/peterwilliams97/twitter_bot/blob/master/results/false.negatives.filtered.latest) 
filtering.)

When our classification model is peforming well enough we run `python do_classify.py -m` to save it.

At this stage we run `python do_twitter.py 30 -r` and see how the twitter-bot performs 
[interacting with people](http://twitter.com/OwwwPapercut/favorites) on twitter.

The Classifier
--------------  
The classifier we use to predict whether tweets are about paper cuts is 
[BayesClassifier.py](https://github.com/peterwilliams97/twitter_bot/blob/master/BayesClassifier.py). This is a simple
[n-gram](http://www.mit.edu/~6.863/spring2011/readings/ngrampages.pdf) classifier.

The n-grams for the paper cut tweets are 
[here](https://raw.github.com/peterwilliams97/twitter_bot/master/data/owww_papertcut.ngram). The most influential are

    TRIGRAMS
    [  0, 98] 98.0 '[TAG_START] i got'
    [  0, 47] 47.0 '[TAG_START] just got'
    [  0, 34] 34.0 'on my finger'
    ...
    [347,  0] -347.0 'featured in papercut'
    [348,  0] -348.0 'in papercut magazine'
    [350,  0] -350.0 'papercut magazine !'
    
    BIGRAMS
    [  0, 34] 34.0 'gave myself'
    [  0, 18] 18.0 'cut ouch'
    [  0, 17] 17.0 'gota paper'
    ...
    [347,  0] -347.0 'featured in'
    [350,  0] -350.0 'magazine !'
    [373,  0] -373.0 'papercut magazine'
    
    UNIGRAMS
    [  0, 14] 14.0 'remover'
    [  0,  9]  9.0 'fuckin'
    [  0,  8]  8.0 'polish'
    ...
    [338,  0] -338.0 'hoping'
    [347,  0] -347.0 'featured'
    [347,  0] -347.0 'request'

Results
-------
The latest internal test results are 
[here](https://github.com/peterwilliams97/twitter_bot/blob/master/results/).

Results from the 
[My week on twitter](https://twitter.com/OwwwPapercut/status/242424216367034370) bot: 
* 408 retweets received
* 54 new followers
* 303 mentions 

Recent [mentions](https://twitter.com/#!/search/realtime/%40owwwpapercut).

Some [positive tweets](https://twitter.com/OwwwPapercut/favorites).

Someone [tweeting](http://bit.ly/RAq4hG) about the Twitter-bot. 

A [man](http://twitter.com/devinkieper/status/242828432306745344) telling the Twitter-bot not to tweet
to his girlfried

A comparison with a [tweeter from the office](http://twitter.com/OwwwPapercut/status/242785630243938304).

Paper cut empathee's [remorse](http://twitter.com/skyformation/status/243065180781674496)