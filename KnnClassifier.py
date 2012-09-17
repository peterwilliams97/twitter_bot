from __future__ import division
# -*- coding:iso-8859-1 -*-
"""
    A basic KNN classifier
    
    http://nlp.stanford.edu/IR-book/pdf/14vcat.pdf
    
    The basic idea here is to represent each document as a vector of counts 
    of ngrams.
    
        - The vectors are normalized to length 1
        - New documents are classifier according the N training documents they are closest to.
        - In the current implementation, the distance measure is cosine.
    
    This does not seem to be well-suited to tweet classification as the
    vectors are all sparse with element values rarely greater than 1.

"""
import math, heapq
import preprocessing

class KnnClassifier:

    N = 4
    
    # N = 4    
    # Precision = 0.796, Recall = 0.843, F1 = 0.819
    weight_bigrams = 3.0195
    weight_trigrams = 9.8414
    backoff = 0.8000
    threshold = 0.2333
    
    weight_bigrams = 3.842
    weight_trigrams = 11.921
    backoff = 0.749
    threshold = 0.644
    
    @staticmethod
    def set_params(weight_bigrams, weight_trigrams, backoff, threshold):
        KnnClassifier.weight_bigrams = weight_bigrams
        KnnClassifier.weight_trigrams = weight_trigrams   
        KnnClassifier.backoff = backoff   
        KnnClassifier.threshold = threshold   

    @staticmethod    
    def get_params():
        return (
            KnnClassifier.weight_bigrams, 
            KnnClassifier.weight_trigrams,  
            KnnClassifier.backoff, 
            KnnClassifier.threshold            
        )
    
    @staticmethod    
    def get_param_names(): 
        return (
            'weight_bigrams',
            'weight_trigrams',
            'backoff',  
            'threshold'  
        ) 
    
    @staticmethod
    def get_weights():
        weights = {
            1 : 1.0, 
            2 : KnnClassifier.weight_bigrams, 
            3 : KnnClassifier.weight_trigrams
        }
        total = sum(weights.values())
        return dict((n,w/total) for n,w in weights.items()) 
    
    @staticmethod
    def build_inv_index(documents):
        """Build an inverted index of the documents.
            inv_index[word][i] = number of occurences of word in documents[i]
        """
        
        inv_index = {}
  
        for i,(_,doc) in enumerate(documents):
            for word in doc:
                if not word in inv_index.keys():
                    inv_index[word] = {}
                inv_index[word][i] = inv_index[word].get(i,0) + 1

        return inv_index
       
    @staticmethod
    def compute_tfidf(documents):
        """Build a tf-idf dict for documents
            tfidf[word][i] = tf-idf for word and document with index i
        """
        
        inv_index = KnnClassifier.build_inv_index(documents)
       
        tfidf = {}
        logN = math.log(len(documents), 10)
 
        for word in inv_index:
            # word_doc_counts[i] = number of occurences of word in documents[i]
            word_doc_counts = inv_index[word] 
            # inverse document frequency ~ -log10(number of documents that word occurs in)
            idf = logN - math.log(len(word_doc_counts), 10)
            for doc_idx,word_count in word_doc_counts.items():
                if word not in tfidf:
                    tfidf[word] = {}
                # term frequency ~ log10(number of occurrences of word in doc)    
                tf = 1.0 + math.log(word_count, 10)
                tfidf[word][doc_idx] = tf * idf 
       
        # Calculate per-document l2 norms for use in cosine similarity
        # tfidf_l2norm[d] = sqrt(sum[tdidf**2])) for tdidf of all words in 
        # document number d
        tfidf_l2norm2 = {}
        for word, doc_indexes in tfidf.items():
            for doc_idx,val in doc_indexes.items():
                tfidf_l2norm2[doc_idx] = tfidf_l2norm2.get(doc_idx, 0.0) + val ** 2
        tfidf_l2norm = dict((doc_idx,math.sqrt(val)) for doc_idx,val in tfidf_l2norm2.items())   

        # Normalize docs to unit length
        for word, doc_indexes in tfidf.items():
            for doc_idx in doc_indexes.keys():
                #assert tfidf_l2norm[doc_idx], '%d : %s' % (doc_idx, documents[doc_idx])
                tfidf[word][doc_idx] /= tfidf_l2norm[doc_idx]
                
        return tfidf

    @staticmethod
    def get_query_vec(ngrams):
        # Construct the query vector as a dict word:log(tf)
        query_vec = {}
        for word in ngrams: 
            query_vec[word] = query_vec.get(word,0) + 1
        return dict((word, math.log(query_vec[word], 10) + 1.0) for word in query_vec)
        
    @staticmethod
    def get_distance(vocab, tfidf, doc_id, query_vec):
        # Return the distance between query_vec and doc_vec
        # Return the cosine    
        # ~!@# Assume some normalization somewhere
        words = [w for w in query_vec if w in vocab]
        return sum(query_vec[w] * tfidf[w].get(doc_id, 0) for w in words)    
    
    def __init__(self, training_data):
        """KnnClassifier initialization

        """

        self.documents = dict((n,[]) for n in (1,2,3))
        self.vocab = dict((n,set()) for n in (1,2,3))
        self.tfidf = dict((n,set()) for n in (1,2,3))
       
        self.train(training_data)
        
    def __repr__(self):
        
        def show_pos_neg(n, vocab, pos_centroid, neg_centroid):
            def pn(word):
                p = pos_centroid.get(word, 0.0)
                n = neg_centroid.get(word, 0.0)
                return '%6.4f - %6.4f = %7.4f %s' % (p, n, p-n, word)
            def order(word):
                return neg_centroid.get(word, 0.0) - pos_centroid.get(word, 0.0)
            return 'pos neg n=%d\n%s' % (n, '\n'.join(pn(word) for word in sorted(vocab, key = order)))
        
        return '\n'.join(show_pos_neg(n, self.vocab[n], self.pos_centroid[n], self.neg_centroid[n]) 
            for n in (3,2,1)) 

    def _add_example(self, cls, message):
        """Add a training example
        """

        words = preprocessing.extract_words(message)
        if not words:  # Treat cases where 'paper cut' is pre-processing as negatives. 
            return

        # Update self.documents[n] and self.vocab[n] for ngrams   and cls
        for n in (1,2,3):
            ngrams = preprocessing.get_ngrams(n, words)
            self.documents[n].append((cls,ngrams))
            for g in ngrams:
                self.vocab[n].add(g)

    def train(self, training_data):
        for cls,message in training_data:
            self._add_example(cls, message)
            
        for n in (1,2,3):
            self.tfidf[n] = KnnClassifier.compute_tfidf(self.documents[n])  

    def classify(self, message, detailed=False):
        """ 
            'message' is a string to classify. Return True or False classification.
            
            Method is to calculate a log_odds from a liklihood based on
            trigram, bigram and unigram (p,n) counts in the training set
            For each trigram
                return smoothed trigram score if trigram in training set, else
                for the 2 bigrams in the trigram
                    return smoothed bigram score if bigram in training set, else
                    for the 2 unigrams in the bigram
                        return smoothed unigram score
                        
            get_score() shows the smoothed scoring    
            <n>gram_score() shows the backoff and smoothing factors    
        """

        def get_docs_with_terms(vocab, tfidf, ngrams):
            docs = set()
            for term in ngrams:
                if term in vocab:
                    docs |= set(tfidf[term].keys())
            return docs
            
        def get_nearest(N, documents, vocab, tfidf, doc_ids, query_vec):
            """Return doc ids of N documents nearest query_vec
            """
            # Compute scores and add to a priority queue
            scores = []
            for i in doc_ids:
                heapq.heappush(scores, (KnnClassifier.get_distance(vocab, tfidf, i, query_vec), i, documents[i][0]))
            # Return top N scores
            return [(cls,i,dist) for dist,i,cls in heapq.nlargest(N,scores)]

        words = preprocessing.extract_words(message)
        if not words:
            return False, 0.0
            
        ngrams = dict((n,preprocessing.get_ngrams(n, words)) for n in (1,2,3))
       
        query_vecs = dict((n, KnnClassifier.get_query_vec(ngrams[n])) for n in (1,2,3))
        
          
        #print message
        
        diffs = {}    
        for n in (1,2,3):
            doc_ids = get_docs_with_terms(self.vocab[n], self.tfidf[n], ngrams[n])
            nearest = get_nearest(KnnClassifier.N, self.documents[n], self.vocab[n], self.tfidf[n], doc_ids, query_vecs[n])
            #print '%d ----' % n
            #print query_vecs[n]
            #for cls,i,dist in nearest:
            #    print '%5s %3d %7.4f %s' % (cls,i,dist, sorted(self.documents[n][i][1])[:10])
            
            #pos = sum(1 if cls else -1 for cls,_,_ in nearest)
            pos = sum((1 if cls else -1) * (KnnClassifier.backoff ** i) for i,(cls,_,_) in enumerate(nearest))
            diffs[n] = pos/KnnClassifier.N 
        #exit()
       
        weights = KnnClassifier.get_weights()   
        diff = sum(diffs[n]*weights[n] for n in (1,2,3))      
 
        #print '--', pos_distance, neg_distance, diff
        return diff > KnnClassifier.threshold, diff

if __name__ == '__main__':
    # Just dump the KnnClassifier class to stdout  
    for k in sorted(KnnClassifier.__dict__):
        print '%20s : %s' % (k, BayesClassifier.__dict__[k])
    
