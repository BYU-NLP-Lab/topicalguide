'''
Created on May 10, 2011

@author: Josh Hansen
'''

import sqlite3
class PmiDb2(object):
    def __init__(self, filename,isolation_level=None):
        self.conn = sqlite3.connect(filename,isolation_level=isolation_level)
        self.c = self.conn.cursor()
    
    def init(self):
        self.c.execute('CREATE TABLE IF NOT EXISTS word_counts(word primary key, count integer);')
        self.c.execute('CREATE TABLE IF NOT EXISTS cooccurrence_counts(word1, word2, count integer);')
    
    def index(self):
        self.c.execute('CREATE INDEX co1 on cocounts.word1;')
        self.c.execute('CREATE INDEX co2 on cocounts.word2;')
        self.c.execute('CREATE INDEX co_joint on (cocounts.word1,cocounts.word2);')

    
    def set_count(self, word, count):
#        print "c("+word+")="+str(count)
        self.c.execute('''insert into word_counts (word,count) values("%s",%s);''' % (word,count))
    
    def set_cocount(self, word1, word2, count):
#        print "c("+word1+","+word2+")="+str(count)
        self.c.execute('''insert into cocounts (word1,word2,count) values("%s","%s",%s);''' % (word1,word2,count))
    