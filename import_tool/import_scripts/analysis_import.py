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

import codecs
import os
import sys

from collections import defaultdict
from datetime import datetime

from django.db import connection, transaction

from topic_modeling.visualize.models import Analysis, Dataset, Topic
from import_scripts.metadata import Metadata
from topic_modeling import settings
from topic_modeling.visualize.models import Document
from topic_modeling.tools import TimeLongThing
import logging

from import_tool.config import config

logger = logging.getLogger('console')

def check_analysis(analysis_name, dataset_name):
    try:
        dataset = Dataset.objects.get(name=dataset_name)
    except Dataset.DoesNotExist:
        return False
    try:
        analysis = Analysis.objects.get(name=analysis_name, dataset=dataset)
    except Analysis.DoesNotExist:
        return False
    return check_analysis_good(analysis)

def check_analysis_good(analysis):
    if not analysis.topics.count():
        logger.warn('No topics defined for this analysis')
        return False
    for topic in analysis.topics.all():
        if not topic.tokens.count():
            logger.warn('A Topic with no tokens: %s' % topic)
            return False
    return True

def remove_analysis(analysis):
    '''Take care of removing the analyis'''
    try:
        analysis.delete()
        return True
    except:
        return Analysis.objects.raw('delete from visualize_analysis where id=%s', [analysis.pk])

def import_analysis(dataset_name, analysis_name, analysis_readable_name, analysis_description,
       markup_dir, state_file, tokenized_file, metadata_filenames, token_regex):
    print >> sys.stderr, u"analysis_import({0})".\
            format(u', '.join([dataset_name, analysis_name,
                analysis_readable_name, analysis_description,
       markup_dir, state_file, tokenized_file, unicode(metadata_filenames), token_regex]))
    start_time = datetime.now()
    print >> sys.stderr, 'Starting time:', start_time
    if settings.database_type()=='sqlite3':
        # These are some attempts to make the database access a little faster
        cursor = connection.cursor()
        cursor.execute('PRAGMA temp_store=MEMORY')
        cursor.execute('PRAGMA synchronous=OFF')
        cursor.execute('PRAGMA cache_size=2000000')
        cursor.execute('PRAGMA journal_mode=MEMORY')
        cursor.execute('PRAGMA locking_mode=EXCLUSIVE')
    
    dataset = Dataset.objects.get(name=dataset_name)
    try:
        analysis = Analysis.objects.get(name=analysis_name, dataset=dataset)
        if check_analysis_good(analysis):
            logger.info('Analysis %s already present and intact. aborting' % analysis_name)
            return False
        else:
            remove_analysis(analysis)
    except Analysis.DoesNotExist:
        pass

    analysis = create_analysis(dataset, analysis_name, analysis_readable_name, analysis_description)
    
    if not os.path.exists(markup_dir):
        print >> sys.stderr, 'Creating markup directory ' + markup_dir
        os.mkdir(markup_dir)
    
    document_metadata = Metadata(metadata_filenames['documents'])
    _load_analysis(analysis, state_file, document_metadata, tokenized_file, token_regex)

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

def create_analysis(dataset, analysis_name, analysis_readable_name, analysis_description):
    """Create the Analysis database object.
    """
    analysis = Analysis(dataset=dataset, name=analysis_name,
                       readable_name=analysis_readable_name, description=analysis_description)
    analysis.save()
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

def create_topics(analysis, num_topics):
    topics = [Topic(number=i, analysis=analysis) for i in range(num_topics)]
    Topic.objects.bulk_create(topics)
    return Topic.objects.filter(analysis=analysis).order_by('number')

def _load_analysis(analysis, state_file, document_metadata, tokenized_file, token_regex):
    '''state_file == the mallet output file'''
    print >> sys.stderr, 'importing analysis'
    prev_docpath = None
    tokens = None
    next_token_idx = 0

    # create the topics
    logger.info('Creating all topics')
    # analysis.topics.delete()
    topics = create_topics(analysis, config['num_topics'])
    logger.info('Topics created')

    iterator = _state_file_iterator(state_file, analysis.dataset.files_dir)
    timer = TimeLongThing(iterator.next(), minor=500, major=10000)
    bad_docs = set()
    with transaction.commit_on_success():
        for i, (docpath, topic_num, word, token_pos, word_type) in enumerate(iterator):
            timer.inc()
            sys.stderr.flush()
            if docpath in bad_docs:
                continue
            if prev_docpath is None or prev_docpath != docpath:
                filename = docpath
                if docpath.startswith('file:'):
                    filename = docpath[len('file:'):]
                try:
                    doc = analysis.dataset.documents.get(full_path=filename)
                except Document.DoesNotExist:
                    logger.err('fail! no document by that name: %s' % docpath)
                    break
                tokens = doc.tokens.order_by('token_index').all()
                if not tokens.count():
                    logger.warn('Document has no tokens: %s %d' % (docpath, doc.pk))
                    bad_docs.add(docpath)
                    continue
                prev_docpath = docpath
                next_token_idx = 0

            topic = topics[topic_num]
            if token_pos >= len(tokens):
                logger.err('an incredible thing; more tokens than tokens %d %d %s'
                        % (token_pos, len(tokens), tokens[-10:]))
                continue
            token = tokens[token_pos]
            token.topics.add(topic)

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

