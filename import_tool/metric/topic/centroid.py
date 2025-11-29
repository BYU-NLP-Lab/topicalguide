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
class AbstractCentroidFinder(object):
    def __init__(self, countsfile, n=20):
        self.db = PmiDb(countsfile, isolation_level="DEFERRED")
        self.n = n

    def topic_summary(self, topic):
        s = 'Topic ' + str(topic.number)
        for tw in sorted(topic.topicword_set.all(),key=lambda x:x.count,reverse=True)[0:20]:
            s += "\t"+tw.word.type + ": " + str(tw.count)
        return s

    def print_status(self, weighted_sums, n=None):
        self._print_status(self._best(weighted_sums), n if n else self.n)
    
    def _best(self, weighted_sums):
        return sorted(weighted_sums.items(), key=lambda x:x[1], reverse=True)
    
    def _print_status(self, best, n):
        print str(best[0:n])

    def save(self, topic, weighted_sums):
        best = self._best(weighted_sums)
        self._print_status(best, self.n)
        print
        
        f = open(environ['HOME'] + '/Projects/topicalguide/output/centroids/{0}_{1}_{2}.txt'.format(topic.analysis.dataset.name,topic.analysis.name,topic.number), 'w')
        f.write(self.topic_summary(topic))
        f.write('\n')
        for word,count in best:
            f.write(word)
            f.write(',')
            f.write(str(count))
            f.write('\n')
        f.close()

class CentroidFinder(AbstractCentroidFinder):
    def centroids(self, topic, min_word_count=1.0, min_cocount=3):
        topic_words = topic.topicword_set.select_related().order_by('-count')
        weighted_sums = dict()
        
        total_counts = self.db.total_counts()
        total_cocounts = self.db.total_cocounts()
        
        for tw in topic_words:
            type = tw.word.type
            weight = float(tw.count)
            print 'word "{0}", weight {1}'.format(type, weight)
#            print 'Relevant pairs: {0}'.format(self.db.word_pair_count(type,min_count=min_cocount))
            
            skipped_words = 0
            skipped_cocounts = 0
            for i,(word1,word2,cocount) in enumerate(self.db.word_pairs(type,min_count=min_cocount,notequal=True)):
                cocount = float(cocount)
                if cocount < min_cocount:
                    skipped_cocounts += 1
                else:
                    p_joint = cocount / total_cocounts
                    word = word1 if type == word2 else word2
                    if i % 1000 == 0:
                        print word,
                        sys.stdout.flush()
                        if i % 5000 == 0 and i > 0: print i,
                    
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
                            weighted_pmi = weight * pmi
                            
                            try:
                                previous_sum = weighted_sums[word]
                            except KeyError:
                                previous_sum = 0.0
                            weighted_sums[word] = previous_sum + weighted_pmi
            print
            print 'Pairs skipped for lack of word counts: ' + str(skipped_words)
            print 'Pairs skipped for lack of cocounts: ' + str(skipped_cocounts)
            self.print_status(weighted_sums)
            print
        self.save(topic, weighted_sums)
        print

class UnifiedPassCentroidFinder(AbstractCentroidFinder):
    def centroids(self, topic, min_word_count=1.0, min_cocount=3.0):
        total_counts = self.db.total_counts()
        total_cocounts = self.db.total_cocounts()
        
        topic_words = topic.topicword_set.select_related().order_by('-count')
        topic_word_weights = dict()
        for tw in topic_words:
            topic_word_weights[tw.word.type] = tw.count
        topic_word_types = topic_word_weights.keys()
        
        weighted_sums = dict()
        def increment(topic_word, other_word):
            weighted_pmi = topic_word_weights[topic_word] * pmi
            
            try:
                previous_sum = weighted_sums[other_word]
            except KeyError:
                previous_sum = 0.0
            weighted_sums[other_word] = previous_sum + weighted_pmi
        
        def count_pair(word1, word2, pmi):
            if word1 in topic_word_types:
                increment(word1, word2)
            if word2 in topic_word_types:
                increment(word2, word1)
        
#        print 'Relevant pairs: {0}'.format(self.db.word_pair_count(topic_word_types,min_count=min_cocount))
            
        skipped_words = 0
        skipped_cocounts = 0
        for i,(word1,word2,cocount) in enumerate(self.db.word_pairs(topic_word_types,min_count=min_cocount)):
            cocount = float(cocount)
            if word1 != word2:
                if cocount < min_cocount:
                    skipped_cocounts += 1
                else:
                    p_joint = cocount / total_cocounts
                    if i % 10000 == 0:
                        print '({0},{1})'.format(word1,word2),
                        sys.stdout.flush()
                        if i % 100000 == 0 and i > 0:
                            print '\n{0}',
                            self.print_status(weighted_sums,n=5)
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
                            count_pair(word1, word2, pmi)
        print
        print 'Pairs skipped for lack of word counts: ' + str(skipped_words)
        print 'Pairs skipped for lack of cocounts: ' + str(skipped_cocounts)
        self.save(topic, weighted_sums)
        print

if __name__ == '__main__':
    cf = CentroidFinder(environ['HOME']+'/Data/wikipedia.org/wikipedia_counts4.sqlite3')
    
    a = Analysis.objects.get(name='lda100topics', dataset__name='state_of_the_union')
    topics = [x for x in a.topics.all()]#.order_by('number')
    random.shuffle(topics)
    for topic in topics:
        print 'Topic ' + str(topic.number)
        for tw in sorted(topic.topicword_set.all(),key=lambda x:x.count,reverse=True)[0:20]:
            print "\t"+tw.word.type + ": " + str(tw.count)
        cf.centroids(topic)
