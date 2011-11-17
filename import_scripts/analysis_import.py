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
from build.common.util import create_dirs_and_open

from django.db import connection, transaction

from topic_modeling.visualize.models import Analysis, Dataset
from topic_modeling.visualize.models import AttributeValueTopic
from topic_modeling.visualize.models import Document
from topic_modeling.visualize.models import DocumentTopic
from topic_modeling.visualize.models import DocumentTopicWord
from topic_modeling.visualize.models import MarkupFile
from topic_modeling.visualize.models import Topic
from topic_modeling.visualize.models import TopicWord
from import_scripts.metadata import Metadata, import_topic_metadata,\
    import_analysis_metadata

NUM_DOTS = 100

def import_analysis(dataset_name, analysis_name, analysis_readable_name, analysis_description,
       markup_dir, state_file, tokenized_file, metadata_filenames, token_regex):
    print >> sys.stderr, "analysis_import({0})".\
            format(', '.join([dataset_name, analysis_name, analysis_readable_name, analysis_description,
       markup_dir, state_file, tokenized_file, str(metadata_filenames), token_regex]))
    start_time = datetime.now()
    print >> sys.stderr, 'Starting time:', start_time
    # These are some attempts to make the database access a little faster
    cursor = connection.cursor()
    cursor.execute('PRAGMA temp_store=MEMORY')
    cursor.execute('PRAGMA synchronous=OFF')
    cursor.execute('PRAGMA cache_size=2000000')
    cursor.execute('PRAGMA journal_mode=MEMORY')
    cursor.execute('PRAGMA locking_mode=EXCLUSIVE')
    
    dataset, _ = Dataset.objects.get_or_create(name=dataset_name)
    analysis, created = _create_analysis(dataset, analysis_name, analysis_readable_name, analysis_description)
    dataset = analysis.dataset
    
    if not os.path.exists(markup_dir):
        print >> sys.stderr, 'Creating markup directory ' + markup_dir
        os.mkdir(markup_dir)
    
    if created:
        doc_index = _doc_index(dataset)
        document_metadata = Metadata(metadata_filenames['documents'])
        
#        attr_table = _parse_document_attributes(dataset, metadata_filenames['datasets'])
        doc_topic_counts, \
        topic_word_counts, \
        doc_topic_word_counts, \
        attr_val_topic_counts, \
        topic_counts, \
        word_index = _parse_mallet_file(analysis, state_file, document_metadata, tokenized_file, token_regex)

        topic_names = _default_topic_names(topic_word_counts)
        topic_index = _create_topic_table(analysis, topic_counts, topic_names)

        _create_doctopic_table(doc_topic_counts, doc_index, topic_index)
        _create_topicword_table(topic_word_counts, topic_index, word_index)
        _create_doctopicword_table(doc_topic_word_counts, doc_index, topic_index, word_index)
        _create_attrvaltopic_table(dataset, attr_val_topic_counts, topic_index)
        
        
        # --- Import Metadata ---
        analysis_metadata = Metadata(metadata_filenames['analyses'])
        import_analysis_metadata(analysis, analysis_metadata)
        
        topic_metadata = Metadata(metadata_filenames['topics'])
        import_topic_metadata(analysis, topic_metadata)

        end_time = datetime.now()
        print >> sys.stderr, 'Finishing time:', end_time
        print >> sys.stderr, 'It took', end_time - start_time,
        print >> sys.stderr, 'to import the analysis'

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


@transaction.commit_manually
def _create_topic_table(analysis, topic_counts, topic_names):
    num_per_dot = max(1, int(len(topic_counts)/NUM_DOTS))
    print >> sys.stderr, 'Creating the Topic Table (%d topics per dot)' % (
            num_per_dot),
    sys.stdout.flush()
    start = datetime.now()
    num_so_far = 0
    topic_index = dict()
    for topic,count in topic_counts.items():
        name = topic_names[topic]
        num_so_far += 1
        if num_so_far % num_per_dot == 0:
            print >> sys.stderr, '.',
            sys.stdout.flush()
        t = Topic(number=topic, analysis=analysis, name=name,
                total_count=count)
        t.save()
        topic_index[topic] = t
    transaction.commit()
    end = datetime.now()
    print >> sys.stderr, '  Done', end - start
    return topic_index


@transaction.commit_manually
def _create_doctopic_table(doctopic, doc_index, topic_index):
    num_per_dot = max(1, int(len(doctopic)/NUM_DOTS))
    print >> sys.stderr, 'Creating the DocumentTopic table',
    print >> sys.stderr, '(%d entries per dot)' % (num_per_dot),
    sys.stdout.flush()
    num_so_far = 0
    start = datetime.now()
    for filename, topic in doctopic:
        num_so_far += 1
        if num_so_far % num_per_dot == 0:
            print >> sys.stderr, '.',
            sys.stdout.flush()
        doc = doc_index[filename]
        t = topic_index[topic]
        count = doctopic[(filename, topic)]
        dt = DocumentTopic(document=doc, topic=t, count=count)
        dt.save()
    transaction.commit()
    end = datetime.now()
    print >> sys.stderr, '  Done', end-start


@transaction.commit_manually
def _create_topicword_table(topicword, topic_index, word_index):
    num_per_dot = max(1, int(len(topicword)/NUM_DOTS))
    print >> sys.stderr, 'Creating the TopicWord table (%d entries per dot)' % (
            num_per_dot),
    sys.stdout.flush()
    num_so_far = 0
    start = datetime.now()
    for topic, word in topicword:
        num_so_far += 1
        if num_so_far % num_per_dot == 0:
            print >> sys.stderr, '.',
            sys.stdout.flush()
        t = topic_index[topic]
        w = word_index[word]
        count = topicword[(topic, word)]
        tw = TopicWord(topic=t, word=w, count=count)
        tw.save()
    transaction.commit()
    end = datetime.now()
    print >> sys.stderr, '  Done', end-start


@transaction.commit_manually
def _create_doctopicword_table(doctopicword, doc_index, topic_index, word_index):
    num_per_dot = max(1, int(len(doctopicword)/NUM_DOTS))
    print >> sys.stderr, 'Creating the DocumentTopicWord table',
    print >> sys.stderr, '(%d entries per dot)' % (num_per_dot),
    sys.stdout.flush()
    num_so_far = 0
    start = datetime.now()
    for filename, topic, word in doctopicword:
        num_so_far += 1
        if num_so_far % num_per_dot == 0:
            print >> sys.stderr, '.',
            sys.stdout.flush()
        doc = doc_index[filename]
        t = topic_index[topic]
        w = word_index[word]
        count = doctopicword[(filename, topic, word)]
        dtw = DocumentTopicWord(document=doc, topic=t, word=w, count=count)
        dtw.save()
    transaction.commit()
    end = datetime.now()
    print >> sys.stderr, '  Done', end-start


@transaction.commit_manually
def _create_attrvaltopic_table(dataset, attrvaltopic, topic_index):
    attr_index = _attribute_index(dataset)
    val_index = _value_index(dataset)
    
    num_per_dot = max(1, int(len(attrvaltopic)/NUM_DOTS))
    print >> sys.stderr, 'Creating the AttributeValueTopic Table',
    print >> sys.stderr, '(%d entries per dot)' % (num_per_dot),
    sys.stdout.flush()
    start = datetime.now()
    num_so_far = 0
    for (attribute, value, topic),count in attrvaltopic.items():
        num_so_far += 1
        if num_so_far % num_per_dot == 0:
            print >> sys.stderr, '.',
            sys.stdout.flush()
        attr = attr_index[attribute]
        val = val_index[(str(value), attribute)] #FIXME? Is there a better way than this str() call?
        t = topic_index[topic]
        avt = AttributeValueTopic(attribute=attr, value=val, topic=t,
                count=count)
        avt.save()
    transaction.commit()
    end = datetime.now()
    print >> sys.stderr, '  Done', end - start


#############################################################################
# Parsing and other intermediate code (not directly modifying the database)
#############################################################################

def _doc_index(dataset):
    doc_index = dict()
    for doc in dataset.document_set.all():
        doc_index[doc.filename] = doc
    return doc_index

def _attribute_index(dataset):
    attr_index = dict()
    for attr in dataset.attribute_set.all():
        attr_index[attr.name] = attr
    return attr_index

def _value_index(dataset):
    value_index = dict()
    for attr in dataset.attribute_set.all():
        for val in attr.value_set.all():
            value_index[(val.value, attr.name)] = val
    return value_index

@transaction.commit_manually
def _parse_mallet_file(analysis, state_file, document_metadata, tokenized_file, token_regex):
    """ Parses the state output file from mallet

    That file lists individual tokens one per line in the following format:

    <document idx> <document id> <token idx> <type idx> <type> <topic>

    The state file is output from MALLET in a gzipped format.  This method
    assumes that the file has already been un-compressed.

    We also create markup files here, so we only have to go through the mallet
    file once.  It makes the code a little more messy, but it saves a lot of
    time when the mallet file is really large.
    """
    print >> sys.stderr, 'Parsing the mallet file and creating markup files...'
    sys.stdout.flush()
    start = datetime.now()
    tokenized_file = codecs.open(tokenized_file, 'r', 'utf-8')
    markup_state = MarkupState(tokenized_file, token_regex)
    doctopic = defaultdict(int)
    topicword = defaultdict(int)
    doctopicword = defaultdict(int)
    attrvaltopic = defaultdict(int)
    topic_counts = defaultdict(int)
    words = set()

    f = codecs.open(state_file, 'r', 'utf-8')
    count = 0
    for line in f:
        count += 1
        if count % 100000 == 0:
            print >> sys.stderr, count
        line = line.strip()
        if line[0] != "#":
            _, docpath, __, ___, word, topic = line.split()
            topic = int(topic)
            # Handle markup file stuff
            if docpath != markup_state.path:
                if markup_state.initialized:
                    markup_state.markup_stop_words()
                    markup_state.output_file(analysis)
                markup_state.initialize(analysis.dataset.files_dir, docpath)
            markup_state.markup_stop_words(word)
            markup_state.markup_word(word, topic)
            # Now other database stuff
            topic_counts[topic] += 1
            words.add(word)
            doctopic[(docpath, topic)] += 1
            topicword[(topic, word)] += 1
            doctopicword[(docpath, topic, word)] += 1
            for attr,value in document_metadata[docpath].items():
                if isinstance(value, list):
                    values_set = value
                else:
                    values_set = [value]
                for value in values_set:
                    attrvaltopic[(attr, value, topic)] += 1
    markup_state.markup_stop_words()
    markup_state.output_file(analysis)
    f.close()

    end = datetime.now()
    print >> sys.stderr, '  Done', end - start
    print >> sys.stderr, 'Populating the word index...',
    start = datetime.now()
    sys.stdout.flush()
    word_index = dict()
    for word in analysis.dataset.word_set.all():
        word_index[word.type] = word
    end = datetime.now()
    transaction.commit()
    print >> sys.stderr, '  Done', end - start
    sys.stdout.flush()
    transaction.commit()
    return doctopic, topicword, doctopicword, attrvaltopic, topic_counts, word_index


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

#############################################################################
# Markup file code
#############################################################################

class MarkupState(object):
    def __init__(self, tokenized_file, token_regex):
        self.path = None
        self.doc_string = None
        self.tokens = None
        self.markup = None
        self.doc_index = 0
        self.token_index = 0
        self.tokenized_file = tokenized_file
        self.initialized = False
        self.token_regex = token_regex

    def initialize(self, files_dir, path):
        self.initialized = True
        self.markup = []
        self.doc_index = 0
        self.token_index = 0
        self.path = path
        self.doc_string = self.read_original_file(files_dir + '/' +
                path)
        token_filename, self.tokens = self.read_token_file()
        while token_filename != path:
            # This is in case a file had all of its words preprocessed out
            old_doc_string = self.doc_string
            old_path = self.path
            self.doc_string = self.read_original_file(files_dir + '/' +
                    token_filename)
            self.markup_stop_words()
            self.output_file()
            token_filename, self.tokens = self.read_token_file()
            self.doc_string = old_doc_string
            self.path = old_path
            self.markup = []
            self.doc_index = 0
            self.token_index = 0

    def read_original_file(self, path):
        return codecs.open(path, 'r', 'utf-8').read().lower()

    def read_token_file(self):
        # This is pretty specific to our file format!
        text = self.tokenized_file.readline()
        text_arr = text.split()
        token_filename, group = text_arr[:2]
        doc_content_only = text[len(token_filename)+len(group)+2:].lower()
        tokens = re.findall(self.token_regex, doc_content_only)
        return token_filename, tokens

    def markup_stop_words(self, word=None):
        '''This assumes that C{word} and the tokens are all in the same case

        If word is None, then we mark the rest of the file as stop words.
        '''
        try:
            def reached_non_stopword():
                if word:
                    return self.tokens[self.token_index] == word
                else:
                    return self.token_index >= len(self.tokens)
            while not reached_non_stopword():
                self.markup_word(self.tokens[self.token_index], 'stop word')
        except IndexError:
            print >> sys.stderr, 'IndexError!'
            for m in self.markup:
                print >> sys.stderr, m
            print >> sys.stderr, self.path
            import traceback
            traceback.print_exc()
            raise

    def markup_word(self, word, topic):
        word_markup = dict()
        word_markup['word'] = word
        word_markup['topic'] = topic
        start_index = self.doc_string.find(word, self.doc_index)
        word_markup['start'] = start_index
        self.markup.append(word_markup)
        self.doc_index = start_index + 1
        self.token_index += 1

    def output_file(self, analysis):
        markup_file_name = '%s-markup/' % analysis.name
        markup_file_name += self.path
        file = create_dirs_and_open(analysis.dataset.dataset_dir + '/' + markup_file_name)
        file.write(anyjson.serialize(self.markup))
        document = Document.objects.get(filename=self.path)
        markup_file = MarkupFile(document=document, analysis=analysis,
                path=markup_file_name)
        markup_file.save()


# vim: et sw=4 sts=4
