'''
Created on May 10, 2011

@author: Josh Hansen
'''


import sys
import random
from os import environ
from math import log

from helper_scripts.pmidb import PmiDb
from topic_modeling.visualize.models import Analysis

environ['DJANGO_SETTINGS_MODULE'] = 'topic_modeling.settings'

class BestValues:
    def __init__(self, n, type='max', key=lambda x:x):
        self.n = n
        self.type = type
        self.key = key
        self.values = []
    
    def _better_than_some(self, value):
        val_key = self.key(value)
        if self.type is 'max':
            for incumbent in reversed(self.values):
                if val_key > self.key(incumbent): return True
            return False
        elif self.type is 'min':
            for incumbent in self.values:
                if val_key < self.key(incumbent): return True
            return False
        else: raise Exception("Unknown optimization type")
    
    def add(self, value):
        still_room = len(self.values) < self.n
        if still_room or self._better_than_some(value):
            self.values.append(value)
            self.values.sort(reverse=True)
            if not still_room:
                self.values.pop()

class CentroidFinder:
    def __init__(self, countsfile):
        self.db = PmiDb(countsfile, isolation_level="DEFERRED")

    def centroids(self, topic, n=10):
        topic_words = topic.topicword_set.select_related()
        i = 0
        best = BestValues(n, key=lambda x:x[1])
#        max = None
#        argmax = None
        for word in self.db.words():
            i += 1
            if i % 10 == 0:
                print word,
                if i % 100 == 0: print
            weighted_sum = self._pmi_weighted_sum(topic_words, word)
            best.add((word,weighted_sum))
#            if max is None or weighted_sum > max:
#                max = weighted_sum
#                argmax = word
#        return argmax
        return best.values
    
    #Note that this is not normalized because we will take the argmax
    def _pmi_weighted_sum(self, topic_words, word1):
        sum = 0.0
        for tw in topic_words:
            word2 = tw.word.type
            p_word2 = float(tw.count)
            pmi = self.db.pmi(word1, word2)
            if pmi is not None:
                sum += p_word2*pmi
        return sum

class CentroidFinder2:
    def __init__(self, countsfile):
        self.db = PmiDb(countsfile, isolation_level="DEFERRED")
    
    def centroids(self, topic, n=20, min_word_count=1.0, min_cocount=3.0):
        topic_words = topic.topicword_set.select_related().order_by('-count')
        weighted_sums = dict()
        
        total_counts = self.db.total_counts()
        total_cocounts = self.db.total_cocounts()
        
        for tw in topic_words:
            type = tw.word.type
            weight = float(tw.count)
            print 'word "{0}", weight {1}'.format(type, weight)
            print 'Relevant pairs: {0}'.format(self.db.word_pair_count(type,min_count=min_cocount))
            
            skipped_words = 0
            skipped_cocounts = 0
            for i,(word1,word2,cocount) in enumerate(self.db.word_pairs(type,min_count=min_cocount)):
                cocount = float(cocount)
                if word1 != word2:
                    if cocount==0:
                        sys.stderr.write('.')
                        skipped_cocounts += 1
                    elif cocount < min_cocount:
                        skipped_cocounts += 1
                    else:
                        p_joint = cocount / total_cocounts
                        word = word1 if type == word2 else word2
                        if i % 1000 == 0:
                            print word,
                            sys.stdout.flush()
                            if i % 20000 == 0: print
                        
                        c_word1 = float(self.db.count(word1))
                        if c_word1 < min_word_count:
                            skipped_words += 1
                        else:
                            p_word1 = c_word1 / total_counts
                            c_word2 = float(self.db.count(word2))
                            if c_word2 < min_word_count:
                                skipped_words += 1
                            else:
                                #total_qualifying_words += 1.0
                                p_word2 = c_word2 / total_counts
                                
                                pmi = log(p_joint) - log(p_word1) - log(p_word2)
                                weighted_pmi = weight * pmi
                                
                                try:
                                    previous_sum = weighted_sums[word]
                                except KeyError:
                                    previous_sum = 0.0
                                weighted_sums[word] = previous_sum + weighted_pmi
            print
            print 'Pairs skipped for lack of word counts: ' + str(skipped_words)
            print 'Pairs skipped for lack of cocounts: ' + str(skipped_cocounts)
            best = sorted(weighted_sums.items(), key=lambda x:x[1], reverse=True)
            print str(best[0:n])
            print
        f = open(environ['HOME'] + '/Projects/topicalguide/output/centroids/' + topic.dataset.name + '_' + str(topic.number) + '.txt', 'w')
        for word,count in best.items():
            f.write(word)
            f.write(',')
            f.write(str(count))
            f.write('\n')
        f.close()
        print

class CentroidFinder3:
    def __init__(self, countsfile):
        self.db = PmiDb(countsfile, isolation_level="DEFERRED")
    
    def centroids(self, topic, n=20, min_word_count=1.0, min_cocount=3.0):
        total_counts = self.db.total_counts()
        total_cocounts = self.db.total_cocounts()
        
        topic_words = topic.topicword_set.select_related().order_by('-count')
        topic_word_weights = dict()
        for tw in topic_words:
            topic_word_weights[tw.word.type] = tw.count
        topic_word_types = topic_word_weights.keys()
        
        weighted_sums = dict()
        def report_status():
            print 'Iteration '+str(i)
            best = sorted(weighted_sums.items(), key=lambda x:x[1], reverse=True)
            print str(best[0:n])
        
        def count_pair(word1, word2, word1count, word2count, pmi):
            def increment(topic_word, other_word, topic_word_weight):
                weighted_pmi = topic_word_weight * pmi
                
                try:
                    previous_sum = weighted_sums[other_word]
                except KeyError:
                    previous_sum = 0.0
                weighted_sums[other_word] = previous_sum + weighted_pmi
            
            if word1 in topic_word_types:
                increment(word1, word2, word1count)
            if word2 in topic_word_types:
                increment(word2, word1, word2count)
        
        print 'Relevant pairs: {0}'.format(self.db.word_pair_count(topic_word_types,min_count=min_cocount))
            
        skipped_words = 0
        skipped_cocounts = 0
        for i,(word1,word2,cocount) in enumerate(self.db.word_pairs(topic_word_types,min_count=min_cocount)):
            cocount = float(cocount)
            if word1 != word2:
                if cocount==0:
                    sys.stderr.write('.')
                    skipped_cocounts += 1
                elif cocount < min_cocount:
                    skipped_cocounts += 1
                else:
                    p_joint = cocount / total_cocounts
                    if i % 1000 == 0:
                        print '({0},{1})'.format(word1,word2)
                        sys.stdout.flush()
                        if i % 20000 == 0: print
                    c_word1 = float(self.db.count(word1))
                    if c_word1 < min_word_count:
                        skipped_words += 1
                    else:
                        p_word1 = c_word1 / total_counts
                        c_word2 = float(self.db.count(word2))
                        if c_word2 < min_word_count:
                            skipped_words += 1
                        else:
                            p_word2 = c_word2 / total_counts
                            pmi = log(p_joint) - log(p_word1) - log(p_word2)
                            count_pair(word1, word2, c_word1, c_word2, pmi)
        print
        print 'Pairs skipped for lack of word counts: ' + str(skipped_words)
        print 'Pairs skipped for lack of cocounts: ' + str(skipped_cocounts)
        best = sorted(weighted_sums.items(), key=lambda x:x[1], reverse=True)
        print str(best[0:n])
        print
        
        f = open(environ['HOME'] + '/Projects/topicalguide/output/centroids/' + topic.dataset.name + '_' + str(topic.number) + '.txt', 'w')
        for word,count in best.items():
            f.write(word)
            f.write(',')
            f.write(str(count))
            f.write('\n')
        f.close()
        print

if __name__ == '__main__':
    cf = CentroidFinder3(environ['HOME']+'/Data/wikipedia.org/wikipedia_counts4.sqlite3')
    
    a = Analysis.objects.get(name='lda100topics', dataset__name='state_of_the_union')
    topics = [x for x in a.topic_set.all()]#.order_by('number')
    random.shuffle(topics)
    for topic in topics:
        print 'Topic ' + str(topic.number)
        for tw in sorted(topic.topicword_set.all(),key=lambda x:x.count,reverse=True)[0:20]:
            print "\t"+tw.word.type + ": " + str(tw.count)
        cf.centroids(topic)
