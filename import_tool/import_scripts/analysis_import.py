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


import time # TODO remove this, only for testing

import codecs
import os
import sys

from collections import defaultdict
from datetime import datetime

from django.db import connections, transaction

from topic_modeling.visualize.models import Analysis, Dataset, Topic
from import_tool.import_scripts.metadata import Metadata
from topic_modeling import settings
from topic_modeling.visualize.models import Document
from topic_modeling.tools import TimeLongThing
import logging

logger = logging.getLogger('root')

def check_analysis(database_id, analysis_name, dataset_name):
    try:
        dataset = Dataset.objects.using(database_id).get(name=dataset_name)
    except Dataset.DoesNotExist:
        return False
    try:
        analysis = Analysis.objects.using(database_id).get(name=analysis_name, dataset=dataset)
    except Analysis.DoesNotExist:
        return False
    return check_analysis_good(analysis)

def check_analysis_good(analysis):
    if not analysis.topics.exists():
        logger.warn('No topics defined for this analysis')
        return False
    for topic in analysis.topics.all():
        if not topic.tokens.exists():
            logger.warn('A Topic with no tokens: %s' % topic)
            return False
    return True

def remove_analysis(database_id, analysis):
    '''Take care of removing the analysis.'''
    try:
        analysis.delete()
        return True
    except:
        return Analysis.objects.using(database_id).raw('delete from visualize_analysis where id=%s', [analysis.pk])

def import_analysis(database_id, dataset_name, analysis_name, analysis_readable_name, analysis_description,
       markup_dir, state_file, tokenized_file, metadata_filenames, token_regex, num_topics):
    # Disabled to keep from cluttering up the CLI
    #~ print >> sys.stderr, u"analysis_import({0})".\
            #~ format(u', '.join([dataset_name, analysis_name,
                #~ analysis_readable_name, analysis_description,
       #~ markup_dir, state_file, tokenized_file, unicode(metadata_filenames), token_regex]))
    start_time = datetime.now()
    print >> sys.stderr, 'Starting time:', start_time
    if settings.database_type(database_id)=='sqlite3':
        # These are some attempts to make the database access a little faster
        cursor = connections[database_id].cursor()
        cursor.execute('PRAGMA temp_store=MEMORY')
        cursor.execute('PRAGMA synchronous=OFF')
        cursor.execute('PRAGMA cache_size=2000000')
        cursor.execute('PRAGMA journal_mode=MEMORY')
        cursor.execute('PRAGMA locking_mode=EXCLUSIVE')
    
    dataset = Dataset.objects.using(database_id).get(name=dataset_name)
    try:
        analysis = Analysis.objects.using(database_id).get(name=analysis_name, dataset=dataset)
        if check_analysis_good(analysis):
            logger.info('Analysis %s already present and intact. aborting' % analysis_name)
            return False
        else:
            remove_analysis(database_id, analysis)
    except Analysis.DoesNotExist:
        pass

    analysis = create_analysis(database_id, dataset, analysis_name, analysis_readable_name, analysis_description)
    
    if not os.path.exists(markup_dir):
        print >> sys.stderr, 'Creating markup directory ' + markup_dir
        os.mkdir(markup_dir)
    
    document_metadata = Metadata(metadata_filenames['documents'])
    _load_analysis(database_id, analysis, state_file, document_metadata, tokenized_file, token_regex, num_topics)

    end_time = datetime.now()
    print >> sys.stderr, 'Finishing time:', end_time
    print >> sys.stderr, 'It took', end_time - start_time,
    print >> sys.stderr, 'to import the analysis'
    
    if settings.database_type()=='sqlite3':
        cursor.execute('PRAGMA journal_mode=DELETE')
        cursor.execute('PRAGMA locking_mode=NORMAL')

#############################################################################
# Database creation code (in the order it's called in main)
#############################################################################

def create_analysis(database_id, dataset, analysis_name, analysis_readable_name, analysis_description):
    """Create the Analysis database object.
    """
    analysis = Analysis(dataset=dataset, name=analysis_name,
                       readable_name=analysis_readable_name, description=analysis_description)
    analysis.save(using=database_id)
    return analysis

WINDOW_SIZE = 30
class TokenNotFound(Exception):
    def __init__(self, word_type, tokens, start_idx, limit):
        self.word_type = word_type
        self.tokens = tokens
        self.start_idx = start_idx
        self.limit = limit
        self.search_window = _search_window(tokens, start_idx, limit)
    
    def __unicode__(self):
        
        return '%s: %s starting at %i with context %s' % \
            (self.__class__.__name__, self.word_type, self.start_idx,
             self.search_window)


_search_range = lambda tokens, start_idx, limit: (start_idx,min(start_idx+limit,len(tokens)))  
def _search_window(tokens, start_idx, limit):
    range_ = _search_range(tokens, start_idx, limit)
    return tokens[range_[0]:range_[1]]

def _find_token(word_type, tokens, start_idx):
    range_ = _search_range(tokens, start_idx, WINDOW_SIZE)
    for token_idx in range(*range_):
        token = tokens[token_idx]
        if token.type.type == word_type:
            return token_idx + 1, token
    # print>>sys.stderr, word_type, len(tokens), start_idx, WINDOW_SIZE
    
    raise TokenNotFound(word_type, tokens, start_idx, WINDOW_SIZE)

def create_topics(database_id, analysis, num_topics):
    topics = [Topic(number=i, analysis=analysis) for i in range(num_topics)] # TODO this would conflict with multiple imports
    Topic.objects.using(database_id).bulk_create(topics) # why doesn't this throw an error for not assigning a primary key?
    return Topic.objects.using(database_id).filter(analysis=analysis).order_by('number')

def _load_analysis(database_id, analysis, state_file, document_metadata, tokenized_file, token_regex, num_topics):
    '''\
    Creates Topics and Topic-Token relationships.
    '''
    topics = create_topics(database_id, analysis, num_topics) # num_topics should be checked against actual topics
    
    
    iterator = _state_file_iterator(state_file, analysis.dataset.files_dir)
    timer = TimeLongThing(iterator.next(), minor=500, major=10000)
    bad_docs = set()
    
    current_doc_path = None # used to track which document we're looking at
    current_doc = None # used to store a Document object, prevent hitting the database
    current_doc_tokens = None # used to store the Document's tokens
    relationships_to_create = {} # used to collect all of the wordtoken_topic relationships, bulk created at the end
    for topic in topics: # add empty list for each topic
        relationships_to_create[topic.number] = []
    current_token = 0
    add_limit = 200
    with transaction.commit_on_success():
        # iterate through mallet output file
        for doc_path, topic_num, word, token_pos, word_type in iterator:
            timer.inc()
            
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
            # collect the tokens associated with each topic
            while current_doc_tokens[current_token].type.type != word:
                current_token += 1
            token = current_doc_tokens[current_token]
            current_token += 1
            relationships_to_create[topic_num].append(token)
            
            # periodically commit to database
            if len(relationships_to_create[topic_num]) > add_limit:
                topics[topic_num].tokens.add(*relationships_to_create[topic_num])
                relationships_to_create[topic_num] = []
            
        # put remaining tokens into the database
        for topic_num, token_list in relationships_to_create.items():
            topics[topic_num].tokens.add(*token_list)

'''Just parse the text and yield it as a tuple per line'''
def _state_file_iterator(state_file, files_dir):
    with codecs.open(state_file, 'r', 'utf-8') as r:
        lines = list(r)
        yield len(lines)
        for _count, line in enumerate(lines):
            line = line.strip()
            if line[0] != "#":
#                print line
                _, docpath, token_pos, word_type, word, topic_num = line.split()
                word = word.lower()
                token_pos = int(token_pos)
                topic_num = int(topic_num)
#                docpath = '%s/%s' % (files_dir, docpath)
                
                yield (docpath, topic_num, word, token_pos, word_type)

def _default_topic_names(topic_word_counts):
    indexed_topic_word_counts = defaultdict(list)

    for (topic, word), count in topic_word_counts.items():
        indexed_topic_word_counts[topic].append((count, word))

    topic_names = dict()
    for topic, top_words in indexed_topic_word_counts.items():
        top_words.sort()
        top_words.reverse()
        name = ' '.join([x[1] for x in top_words][:2])
        topic_names[topic] = name
    return topic_names

