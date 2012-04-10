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
        sql = 'select word from word_counts'
        if min_count:
            sql += ' where count >= '+str(min_count)
        sql += ';'
        print sql
        z = self.conn.cursor().execute(sql)
        for row in z:
            yield row[0]
    
    def words_as_sql_list(self, words):
        if isinstance(words,list):
            words = set(words)
        else:
            words = set([words])
        return "('{0}')".format("','".join(words))
    
    def _word_pair_from_sql(self, required_words, min_count=None, notequal=None):
        if isinstance(required_words, list):
            condition = " in ('{0}')".format("','".join(required_words))
        else:
            condition = "='{0}'".format(required_words)
        count_sql = ' and count >= {0}'.format(min_count) if min_count else ''
        noteq_sql = ' and word1 != word2' if notequal else ''
        return 'from cocounts where (word1{condition} or word2{condition}){count}{noteq};' \
               .format(condition=condition, count=count_sql, noteq=noteq_sql)
    
    def word_pairs(self, required_words, min_count=None, notequal=None):
        sql = 'select word1,word2,count '+self._word_pair_from_sql(required_words, min_count=min_count, notequal=notequal)
        print sql
        z  = self.conn.cursor().execute(sql)
        for row in z:
            yield row[0:3]
    
    def word_pair_count(self, required_words, min_count=None, notequal=None):
        sql = 'select count(*) '+self._word_pair_from_sql(required_words, min_count=min_count, notequal=notequal)
        print sql
        z = self.conn.cursor().execute(sql)
        return z.next()[0]
    
    def set_count(self, word, count):
        self.c.execute('''insert into word_counts (word,count) values("%s",%s);''' % (word,count))
    
    def set_cocount(self, word1, word2, count):
        self.c.execute('''insert into cocounts (word1,word2,count) values("%s","%s",%s);''' % (word1,word2,count))
