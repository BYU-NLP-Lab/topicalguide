'''
Created on May 10, 2011

@author: Josh Hansen
'''

import sqlite3
from math import log

class PmiDb(object):
    def __init__(self, filename, isolation_level=None):
        self.conn = sqlite3.connect(filename,isolation_level=isolation_level)
        self.c = self.conn.cursor()
        
    def init(self):
        self.c.execute('CREATE TABLE IF NOT EXISTS word_counts(word primary key, count integer);')
        self.c.execute('CREATE TABLE IF NOT EXISTS cocounts(word1, word2, count integer);')
    
    def index(self):
        self.c.execute('CREATE INDEX co_word1 on cocounts.word1;')
        self.c.execute('CREATE INDEX co_word2 on cocounts.word2;')
        self.c.execute('CREATE INDEX co_both on (cocounts.word1,cocounts.word2);')
        
    def count(self, word):
        self.c.execute("select count from word_counts where word = '%s';" % word)
        for row in self.c:
            return int(row[0])
        return 0
    
    def total_counts(self):
        z = self.conn.cursor().execute(u'select words from total_counts;')
        return float(z.next()[0])
    
    def prob(self, word):
        return float(self.count(word)) / float(self.total_counts())
    
    def cocount(self, word1, word2):
        arr = sorted([word1,word2])
        return self._cocount(arr[0], arr[1])
    
    def _cocount(self, word1, word2):
        self.c.execute("select count from cocounts where word1='%s' and word2='%s';"
            % (word1,word2))
        for row in self.c:
            return int(row[0])
        return 0
    
#    def _cocount(self, word1, word2):
#        return self._cooccurrence_count(word1, word2)
#        self.c.execute("select count from cocounts where word_pair = '%s,%s';"
#            % (word1,word2))
#        for row in self.c:
#            return int(row[0])
#        return 0
    def total_cocounts(self):
        z = self.conn.cursor().execute(u'select cooccurrences from total_counts;')
        return float(z.next()[0])
    
    def joint_prob(self, word1, word2):
        return float(self.cocount(word1, word2)) / float(self.total_cocounts())
    
    def pmi(self, word1, word2):
        arr = sorted([word1,word2])
        return self._pmi(arr[0], arr[1])
    
    def _pmi(self, word1, word2):
        cocounts = self._cocount(word1, word2)
        if cocounts is 0:
            return None
        return log(cocounts) - log(self.count(word1)) - log(self.count(word2))
    
    def words(self, min_count=None):
        d = self.conn.cursor()
        sql = 'select word from word_counts'
        if min_count:
            sql += ' where count >= '+str(min_count)
        sql += ';'
        d.execute(sql)
        for row in d:
            yield row[0]
            
    def words_as_sql_list(self, words):
        if isinstance(words,list):
            words = set(words)
        else:
            words = set([words])
        return "('{0}')".format("','".join(words))
    
    def word_pairs(self, required_words, min_count=None):
        required_words_list = self.words_as_sql_list(required_words)
        
        sql = 'select word1,word2,count from cocounts where word1 in %s or word2 in %s' % (required_words_list,required_words_list)
        if min_count:
            sql += ' and count >= '+str(min_count)
        sql += ';'
        print sql
        z  = self.conn.cursor().execute(sql)
        
        def gen():
            ended = False
            while not ended:
                try:
                    yield z.next()[0:3]
                except:
                    ended = True
        
        return gen()
    
    def word_pair_count(self, required_words, min_count=None):
        required_words_list = self.words_as_sql_list(required_words)
        sql = 'select count(*) from cocounts where word1 in %s or word2 in %s' % (required_words_list,required_words_list)
        if min_count:
            sql += ' and count >= ' + str(min_count)
        sql += ';'
        z = self.conn.cursor().execute(sql)
        return z.next()[0]
    
    def set_count(self, word, count):
#        print "c("+word+")="+str(count)
        self.c.execute('''insert into word_counts (word,count) values("%s",%s);''' % (word,count))
    
    def set_cocount(self, word1, word2, count):
#        print "c("+word1+","+word2+")="+str(count)
        self.c.execute('''insert into cocounts (word1,word2,count) values("%s","%s",%s);''' % (word1,word2,count))