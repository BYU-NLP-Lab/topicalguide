# The Topical Guide
# Copyright 2010-2011 Brigham Young University
#
# This file is part of the Topical Guide <http://nlp.cs.byu.edu/topic_browser>.
#
# The Topical Guide is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published by the
# Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# The Topical Guide is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public License
# for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with the Topical Guide.  If not, see <http://www.gnu.org/licenses/>.
#
# If you have inquiries regarding any further use of the Topical Guide, please
# contact the Copyright Licensing Office, Brigham Young University, 3760 HBLL,
# Provo, UT 84602, (801) 422-9339 or 422-3821, e-mail copyright@byu.edu.


import time
import codecs
import os
import sys
import logging
from collections import defaultdict
from datetime import datetime

from django.db import connections, transaction

from topic_modeling.visualize.models import Document, Analysis, Dataset, Topic, WordToken_Topics
from topic_modeling import settings
from topic_modeling.tools import TimeLongThing


logger = logging.getLogger('root')

def import_analysis(database_id, dataset_name, analysis_name, analysis_readable_name, analysis_description,
       state_file, tokenized_file, token_regex, num_topics):
    """Import the mallet output into the database."""
    # attempt to make the database access a little faster
    if settings.database_type(database_id)=='sqlite3':
        cursor = connections[database_id].cursor()
        cursor.execute('PRAGMA temp_store=MEMORY')
        cursor.execute('PRAGMA synchronous=OFF')
        cursor.execute('PRAGMA cache_size=2000000')
        cursor.execute('PRAGMA journal_mode=MEMORY')
        cursor.execute('PRAGMA locking_mode=EXCLUSIVE')
    
    # get or create the analysis
    dataset = Dataset.objects.using(database_id).get(name=dataset_name)
    analysis = None
    if Analysis.objects.using(database_id).filter(name=analysis_name, dataset=dataset).exists():
        analysis = Analysis.objects.using(database_id).get(name=analysis_name, dataset=dataset)
    else:
        with transaction.commit_on_success():
            analysis = Analysis.objects.using(database_id)\
                               .create(name=analysis_name,
                                       dataset=dataset, 
                                       readable_name=analysis_readable_name, 
                                       description=analysis_description)
    # create all of the topics if needed
    if not Topic.objects.using(database_id).filter(analysis=analysis).exists():
        with transaction.commit_on_success():
            topics = [Topic(number=i, analysis=analysis) for i in range(num_topics)]
            Topic.objects.using(database_id).bulk_create(topics)
    
    # create the token/word to topic relations
    topics = Topic.objects.using(database_id).filter(analysis=analysis).order_by('number')
    with codecs.open(state_file, 'r', 'utf-8') as r:
        lines = list(r)
        timer = TimeLongThing(len(lines))
        
        bad_docs = set()
        
        current_doc_path = None # used to track which document we're looking at
        current_doc = None # used to store a Document object, prevent hitting the database for each line
        current_doc_tokens = None # used to store the Document's tokens
        relationships_to_create = {} # used to collect all of the wordtoken_topic relationships, bulk created at the end
        for topic in topics: # add empty list for each topic
            relationships_to_create[topic.number] = []
        current_token = 0
        add_limit = 50000 # how many entries to commit to the database at a time
        
        # the items to be committed to the database
        token_topics_to_create = []
        token_topics_id = 0
        if WordToken_Topics.objects.using(database_id).all().exists():
            token_topics_id = WordToken_Topics.objects.using(database_id).all().aggregate(Max('id'))['id__max'] + 1
        
        
        with transaction.commit_on_success():
            # iterate through mallet output file
            for line in lines:
                timer.inc()
                
                # avoid comments
                if line[0] == '#':
                    continue
                
                # parse a line
                ___, doc_path, token_pos, word_type, word, topic_num = line.split()
                word = word.lower()
                token_pos = int(token_pos)
                topic_num = int(topic_num)
                
                
                if doc_path in bad_docs:
                    continue
                
                if doc_path != current_doc_path: # new document encountered
                    current_doc_path = doc_path
                    try:
                        current_doc = analysis.dataset.documents.get(filename=doc_path)
                    except Document.DoesNotExist:
                        # WARNING: the following lines are for backwards compatibility
                        filename = doc_path
                        if doc_path.startswith('file:'):
                            filename = doc_path[len('file:'):]
                        try:
                            current_doc = analysis.dataset.documents.get(full_path=filename)
                        except Document.DoesNotExist:
                            logger.err('No document by name/path: %s/%s' % (doc_path, filename))
                            break
                        # END WARNING
                    
                    current_doc_tokens = list(current_doc.tokens.order_by('token_index').select_related())
                    
                    if not current_doc_tokens:
                        logger.warn('Document has no tokens: %s %d' % (doc_path, doc.pk))
                        bad_docs.add(doc_path)
                        continue
                    
                    current_doc_path = doc_path
                    current_token = 0
                # collect the tokens/words associated with each topic
                while current_doc_tokens[current_token].type.type != word:
                    current_token += 1
                token = current_doc_tokens[current_token]
                current_token += 1
                
                relationship = WordToken_Topics(id=token_topics_id, wordtoken_id=token.id,
                                                topic_id=topics[topic_num].id)
                token_topics_id += 1
                token_topics_to_create.append(relationship)
                
                if len(token_topics_to_create) > add_limit:
                    WordToken_Topics.objects.using(database_id).bulk_create(token_topics_to_create)
                    token_topics_to_create = []
            if len(token_topics_to_create) > add_limit:
                    WordToken_Topics.objects.using(database_id).bulk_create(token_topics_to_create)
                    token_topics_to_create = []
                #~ relationships_to_create[topic_num].append(token)
                #~ 
                #~ # periodically commit to database
                #~ if len(relationships_to_create[topic_num]) > add_limit:
                    #~ topics[topic_num].tokens.add(*relationships_to_create[topic_num])
                    #~ relationships_to_create[topic_num] = []
                #~ 
            #~ # put remaining tokens into the database
            #~ for topic_num, token_list in relationships_to_create.items():
                #~ topics[topic_num].tokens.add(*token_list)
    
    # make it so the database isn't in memory
    if settings.database_type(database_id)=='sqlite3':
        cursor.execute('PRAGMA journal_mode=DELETE')
        cursor.execute('PRAGMA locking_mode=NORMAL')


