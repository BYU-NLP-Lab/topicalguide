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
import json
from collections import defaultdict
from datetime import datetime

from django.db import connections, transaction
from django.db.models import Max

from topic_modeling.visualize.models import Document, Analysis, Dataset, Topic, WordToken_Topics, WordToken
from topic_modeling import settings
from topic_modeling.tools import TimeLongThing


logger = logging.getLogger('root')

def get_or_create_analysis(database_id, dataset_name, analysis):
    """Return Analysis."""
    print(dataset_name)
    dataset_pk = Dataset.objects.using(database_id).get(name=dataset_name).id
    if Analysis.objects.using(database_id).filter(name=analysis.get_identifier(), dataset_id=dataset_pk).exists():
        analysis_db = Analysis.objects.using(database_id).get(name=analysis.get_identifier(), dataset_id=dataset_pk)
    else:
        analysis_db = Analysis.objects.using(database_id).create(name=analysis.get_identifier(),
                                                                 dataset_id=dataset_pk,
                                                                 working_dir_path=analysis.get_working_directory())
    return analysis_db

def has_token_topic_relations(database_id, analysis_db):
    """Determine if the token topic relationships have been populated."""
    for t in Topic.objects.using(database_id).filter(analysis_id=analysis_db.id):
        if t.tokens.exists():
            return True
    return False

def import_analysis(database_id, dataset_name, analysis):
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
    analysis_db = get_or_create_analysis(database_id, dataset_name, analysis)
    
    # create the token to topic relations
    if not has_token_topic_relations(database_id, analysis_db):
        with transaction.commit_on_success(using=database_id):
            bad_docs = set()
            current_doc_name = None
            current_doc = None # used to store a Document object, prevent hitting the database for each line
            current_doc_tokens = None # used to store the Document's tokens
            
            add_limit = 200000 # how many entries to commit to the database at a time
            
            # the Token-Topic relations to be committed to the database
            token_topics_to_create = []
            token_topics_id = 0
            if WordToken_Topics.objects.using(database_id).all().exists():
                token_topics_id = WordToken_Topics.objects.using(database_id).all().aggregate(Max('id'))['id__max'] + 1
            
            # stopwords
            stopwords = analysis.get_stopwords()
            stopword_relations = [] # relations to create with the Analysis
            
            topics = {}
            for t in Topic.objects.using(database_id).filter(analysis_id=analysis_db.id):
                topics[t.number] = t.id
            
            for doc_name, word, topic_num in analysis:
                # avoid documents without any tokens in the database
                if doc_name in bad_docs:
                    continue
                # new document encountered, load WordTokens
                if doc_name != current_doc_name: 
                    current_doc = analysis_db.dataset.documents.get(filename=doc_name)
                    current_doc_tokens = list(current_doc.tokens.order_by('token_index').select_related())
                    if not current_doc_tokens:
                        logger.warn('Document has no tokens: %s %d' % (doc_name, doc.pk))
                        bad_docs.add(doc_name)
                        continue
                    current_doc_name = doc_name
                    current_token = 0
                
                # find the correct WordToken that matches the word
                try:
                    while unicode(current_doc_tokens[current_token].type.type) != word:
                        if current_doc_tokens[current_token].type.type in stopwords:
                            stopword_relations.append(current_doc_tokens[current_token])
                        current_token += 1
                except:
                    print("Not found: %s %s %s" %(doc_name, word, str(topic_num)))
                    current_token = 0
                    continue
                    
                
                # collect the tokens/words associated with each topic
                token = current_doc_tokens[current_token]
                del current_doc_tokens[current_token] # remove what we don't need anymore
                
                if not topic_num in topics:
                    topic = Topic.objects.using(database_id).create(number=topic_num, analysis_id=analysis_db.id)
                    topics[topic_num] = topic.id
                
                relationship = WordToken_Topics(id=token_topics_id, wordtoken_id=token.id,
                                                topic_id=topics[topic_num])
                token_topics_id += 1
                token_topics_to_create.append(relationship)
                
                if len(token_topics_to_create) > add_limit:
                    WordToken_Topics.objects.using(database_id).bulk_create(token_topics_to_create)
                    token_topics_to_create = []
            if len(token_topics_to_create) > 0:
                WordToken_Topics.objects.using(database_id).bulk_create(token_topics_to_create)
                token_topics_to_create = []
            if len(stopword_relations) > 0:
                while len(stopword_relations) > 200:
                    analysis_db.stopwords.add(*stopword_relations[-200:])
                    stopword_relations[-200:] = []
    
    # make it so the database isn't in memory
    if settings.database_type(database_id)=='sqlite3':
        cursor.execute('PRAGMA journal_mode=DELETE')
        cursor.execute('PRAGMA locking_mode=NORMAL')
