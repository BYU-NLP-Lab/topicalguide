'''
Created on May 10, 2011

@author: Josh Hansen
'''

from os import environ
from helper_scripts.pmidb import PmiDb
#from helper_scripts.pmidb2 import PmiDb2

if __name__=='__main__':
    src = environ['HOME']+'/Data/wikipedia.org/wikipedia_counts2.sqlite3'
#    dest = environ['HOME']+'/Data/wikipedia.org/wp_counts_reindexed.sqlite3'
    
    db = PmiDb(src,isolation_level="DEFERRED")
    db.init()
#    dest_db = PmiDb2(dest,isolation_level="DEFERRED")
#    dest_db.init()
    
    interval = 100000
    interval2 = 100
    i = 0
    ii = 0
    
    c = db.conn.cursor()
#    c.execute('select word,count from word_counts;')
#    for row in c:
#        dest_db.set_count(row[0],row[1])
#        
#        i+=1
#        if i >= interval:
#            print '.',
#            dest_db.conn.commit()
#            i = 0
#            ii += 1
#            
#            if ii >= interval2:
#                print
#                ii = 0
    
    c.execute('select word_pair,count from cooccurrence_counts;')
    for row in c:
        words = row[0].split(',')
        db.set_cocount(words[0],words[1],row[1])
        
        i+=1
        if i >= interval:
            print '*',
            db.conn.commit()
            i = 0
            ii += 1
            
            if ii >= interval2:
                print
                print words[0],words[1]
                ii = 0
    db.index()