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
import re
import sys

from collections import defaultdict
from datetime import datetime

import topic_modeling.anyjson as anyjson
from build import create_dirs_and_open

from django.db import connection, transaction

from topic_modeling.visualize.models import Analysis, Dataset, WordType
from topic_modeling.visualize.models import Document
from topic_modeling.visualize.models import Topic
from topic_modeling.visualize.models import TopicWord
from import_scripts.metadata import Metadata
from topic_modeling import settings

NUM_DOTS = 100

def import_analysis(dataset_name, analysis_name, analysis_readable_name, analysis_description,
       markup_dir, state_file, tokenized_file, metadata_filenames, token_regex):
    print >> sys.stderr, u"analysis_import({0})".\
            format(u', '.join([dataset_name, analysis_name, analysis_readable_name, analysis_description,
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
    
    dataset, _ = Dataset.objects.get_or_create(name=dataset_name)
    analysis, created = _create_analysis(dataset, analysis_name, analysis_readable_name, analysis_description)
    
    if not os.path.exists(markup_dir):
        print >> sys.stderr, 'Creating markup directory ' + markup_dir
        os.mkdir(markup_dir)
    
    if created:
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

def _create_analysis(dataset, analysis_name, analysis_readable_name, analysis_description):
    """Create the Analysis database object.
    """
    print >> sys.stderr, 'Creating the analysis...  ',
    analysis, created = Analysis.objects.get_or_create(dataset=dataset, name=analysis_name,
                       readable_name=analysis_readable_name, description=analysis_description)
    print >> sys.stderr, 'Done'
    return analysis, created


#@transaction.commit_manually
def _load_analysis(analysis, state_file, document_metadata, tokenized_file, token_regex):
    for doc,topic,word_type,word_token in _state_file_iterator(analysis, state_file):
        print '%s, %s, %s, %s %s' % (doc.filename, topic.number, word_type.type, word_token.token_index, word_token.start)
    
#    """ Parses the state output file from mallet and stores a representation of it in the database
#
#    That file lists individual tokens one per line in the following format:
#
#    <document idx> <document id> <token idx> <type idx> <type> <topic>
#
#    The state file is output from MALLET in a gzipped format.  This method
#    assumes that the file has already been un-compressed.
#
#    We also create markup files here, so we only have to go through the mallet
#    file once.  It makes the code a little more messy, but it saves a lot of
#    time when the mallet file is really large.
#    """
#    print >> sys.stderr, 'Parsing the mallet file and creating markup files...'
#    sys.stdout.flush()
#    start = datetime.now()
#    tokenized_file = codecs.open(tokenized_file, 'r', 'utf-8')
#    markup_state = MarkupState(analysis, tokenized_file, token_regex)
#
#    f = codecs.open(state_file, 'r', 'utf-8')
#    count = 0
#    for line in f:
#        count += 1
#        if count % 100000 == 0:
#            print >> sys.stderr, count
#        line = line.strip()
#        if line[0] != "#":
#            _, docpath, __, ___, word, topic_num = line.split()
#            topic, _topic_created = analysis.topics.get_or_create(number=topic_num)
#            
#            
#            
#            
#            # Handle markup file stuff
#            if docpath != markup_state.path:
#                if markup_state.initialized:
#                    markup_state.markup_stop_words()
#                    markup_state.output_file(analysis)
#                markup_state.initialize(analysis.dataset.files_dir, docpath)
#            markup_state.markup_stop_words(word)
#            markup_state.markup_word(word, topic)
#            for attr,value in document_metadata[docpath].items():
#                if isinstance(value, list):
#                    values_set = value
#                else:
#                    values_set = [value]
#                for value in values_set:
#                    attrvaltopic[(attr, value, topic)] += 1
#    markup_state.markup_stop_words()
#    markup_state.output_file(analysis)
#    f.close()
#
#    end = datetime.now()
#    print >> sys.stderr, '  Done', end - start
#    print >> sys.stderr, 'Populating the word index...',
#    start = datetime.now()
#    sys.stdout.flush()
#    word_index = dict()
#    for word in analysis.dataset.word_set.all():
#        word_index[word.type] = word
#    end = datetime.now()
#    transaction.commit()
#    print >> sys.stderr, '  Done', end - start
#    sys.stdout.flush()
#    transaction.commit()



'''
    Yields (document,topic,type,token) tuples for each line in a Mallet state file
'''
def _state_file_iterator(analysis, state_file):
    files_dir = analysis.dataset.files_dir
    prior_docpath = None
    token_num = None
    
    f = codecs.open(state_file, 'r', 'utf-8')
    for _count, line in enumerate(f):
        line = line.strip()
        if line[0] != "#":
            print line
            print str(token_num)
            _, docpath, __, ___, word, topic_num = line.split()
            word = word.lower()
            docpath = '%s/%s' % (files_dir, docpath)
            
            if prior_docpath is None or prior_docpath != docpath:
                token_num = 0
                prior_docpath = docpath
            
            doc = analysis.dataset.docs.get(filename=docpath)
            topic, _topic_created = analysis.topics.get_or_create(number=topic_num)
            word_type = WordType.objects.get(type=word)
            word_token = doc.tokens.filter(type=word_type, token_index__gte=token_num).order_by('token_index')[0]
            yield (doc,topic,word_type,word_token)
            token_num = word_token.token_index
            print str(token_num)
            

def _load_analysis2(analysis, state_file, document_metadata, tokenized_file, token_regex):
    doc = None
    prior_docpath = None
    tokens = None
    
    it = _state_file_iterator2(state_file, analysis.dataset.files_dir)
    
    for docpath, topic_num, word in _state_file_iterator2(state_file, analysis.dataset.files_dir):
        if prior_docpath is None or prior_docpath != docpath:
            doc = analysis.dataset.docs.get(filename=docpath)
            tokens = doc.tokens.order_by('token_index').all()
            prior_docpath = docpath

'''Just parse the text and yield it as a tuple per line'''
def _state_file_iterator2(state_file, files_dir):
    f = codecs.open(state_file, 'r', 'utf-8')
    for _count, line in enumerate(f):
        line = line.strip()
        if line[0] != "#":
            print line
            _, docpath, __, ___, word, topic_num = line.split()
            word = word.lower()
            docpath = '%s/%s' % (files_dir, docpath)
            
            yield (docpath, topic_num, word)

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


#class MarkupState(object):
#    def __init__(self, analysis, tokenized_file, token_regex):
#        self.dataset = analysis.dataset
#        self.analysis = analysis
#        self.path = None
#        self.doc_string = None
#        self.tokens = None
##        self.markup = None
#        self.doc_index = 0
#        self.token_index = 0
#        self.tokenized_file = tokenized_file
#        self.initialized = False
#        self.token_regex = token_regex
#
#    def initialize(self, files_dir, path):
#        self.initialized = True
##        self.markup = []
#        self.doc_index = 0
#        self.token_index = 0
#        self.path = path
#        self.doc_string = self.read_original_file(files_dir + '/' +
#                path)
#        self.doc = self.analysis.dataset.documents.get(filename=path)
#        token_filename, self.tokens = self.read_token_file()
#        while token_filename != path:
#            # This is in case a file had all of its words preprocessed out
#            old_doc_string = self.doc_string
#            old_path = self.path
#            self.doc_string = self.read_original_file(files_dir + '/' +
#                    token_filename)
#            self.doc = self.analysis.dataset.documents.get(filename=token_filename)
#            self.markup_stop_words()
#            self.output_file()
#            token_filename, self.tokens = self.read_token_file()
#            self.doc_string = old_doc_string
#            self.path = old_path
##            self.markup = []
#            self.doc_index = 0
#            self.token_index = 0
#
#    def read_original_file(self, path):
#        return codecs.open(path, 'r', 'utf-8').read().lower()
#
#    def read_token_file(self):
#        # This is pretty specific to our file format!
#        text = self.tokenized_file.readline()
#        text_arr = text.split()
#        token_filename, group = text_arr[:2]
#        doc_content_only = text[len(token_filename)+len(group)+2:].lower()
#        tokens = re.findall(self.token_regex, doc_content_only)
#        return token_filename, tokens
#
#    def markup_stop_words(self, word=None):
#        '''This assumes that C{word} and the tokens are all in the same case
#
#        If word is None, then we mark the rest of the file as stop words.
#        '''
#        try:
#            def reached_non_stopword():
#                if word:
#                    return self.tokens[self.token_index] == word
#                else:
#                    return self.token_index >= len(self.tokens)
#            while not reached_non_stopword():
#                self.markup_word(self.token_index, 'stop word')
#        except IndexError:
#            print >> sys.stderr, 'IndexError!'
#            for m in self.markup:
#                print >> sys.stderr, m
#            print >> sys.stderr, self.path
#            import traceback
#            traceback.print_exc()
#            raise
#
#    def markup_word(self, token_index, topic):
#        token, _ = self.dataset.tokens.get_or_create(doc=self.doc, token_index=token_index)
#        
#        token.create(
#        word_markup = dict()
#        word_markup['word'] = word
#        word_markup['topic'] = topic
#        start_index = self.doc_string.find(word, self.doc_index)
#        word_markup['start'] = start_index
#        self.markup.append(word_markup)
#        self.doc_index = start_index + 1
#        self.token_index += 1
#
#    def output_file(self, analysis):
#        markup_file_name = '%s-markup/' % analysis.name
#        markup_file_name += self.path
#        file = create_dirs_and_open(analysis.dataset.dataset_dir + '/' + markup_file_name)
#        file.write(anyjson.serialize(self.markup))
#        document = Document.objects.get(filename=self.path)
#        markup_file = MarkupFile(document=document, analysis=analysis,
#                path=markup_file_name)
#        markup_file.save()


# vim: et sw=4 sts=4
