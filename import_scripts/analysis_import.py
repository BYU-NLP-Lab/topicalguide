# The Topic Browser
# Copyright 2010-2011 Brigham Young University
#
# This file is part of the Topic Browser <http://nlp.cs.byu.edu/topic_browser>.
#
# The Topic Browser is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published by the
# Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# The Topic Browser is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public License
# for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with the Topic Browser.  If not, see <http://www.gnu.org/licenses/>.
#
# If you have inquiries regarding any further use of the Topic Browser, please
# contact the Copyright Licensing Office, Brigham Young University, 3760 HBLL,
# Provo, UT 84602, (801) 422-9339 or 422-3821, e-mail copyright@byu.edu.

import codecs, os, sys
import re
from collections import defaultdict
from datetime import datetime

import topic_modeling.anyjson as anyjson
from build.common.util import create_dirs_and_open

from django.db import connection, transaction

from topic_modeling.visualize.models import Analysis
from topic_modeling.visualize.models import AttributeValueTopic
from topic_modeling.visualize.models import Dataset
from topic_modeling.visualize.models import Document
from topic_modeling.visualize.models import DocumentTopic
from topic_modeling.visualize.models import DocumentTopicWord
from topic_modeling.visualize.models import MarkupFile
from topic_modeling.visualize.models import Topic
from topic_modeling.visualize.models import TopicWord

# A couple of global variables just to make life easier, so I don't have to
# pass them around so much - they're created once and then never change
dataset = None
analysis = None

NUM_DOTS = 100

# This could maybe benefit from the use of a logger, but I didn't care enough
# to put one in, so I just use print statements.

def import_analysis(name, readable_name, description, dataset_name, dataset_attr_file,
        state_file, tokenized_file, files_dir, token_regex):
    print >> sys.stderr, "analysis_import({0}, {1}, {2}, {3}, {4}, {5}, {6})".\
            format(name, readable_name, description, dataset_name, dataset_attr_file,
        state_file, tokenized_file, files_dir, token_regex)
    start_time = datetime.now()
    print >> sys.stderr, 'Starting time:', start_time
    # These are some attempts to make the database access a little faster
    cursor = connection.cursor()
    cursor.execute('PRAGMA temp_store=MEMORY')
    cursor.execute('PRAGMA synchronous=OFF')
    cursor.execute('PRAGMA cache_size=2000000')
    cursor.execute('PRAGMA journal_mode=MEMORY')
    cursor.execute('PRAGMA locking_mode=EXCLUSIVE')

    global dataset
    dataset = Dataset.objects.get(name=dataset_name)
    created = create_analysis(name, readable_name, description)

    if created:
        doc_index, attr_index, value_index, attr_table = parse_attributes(
                dataset_attr_file)
        dt, tw, dtw, avt, topics, word_index = parse_mallet_file(state_file,
                attr_table, tokenized_file, files_dir, token_regex)

        topicinfo = create_topic_info(tw)
        topic_index = create_topic_table(topics, topicinfo)

        create_doctopic_table(dt, doc_index, topic_index)
        create_topicword_table(tw, topic_index, word_index)
        create_doctopicword_table(dtw, doc_index, topic_index, word_index)
        create_attrvaltopic_table(avt, attr_index, value_index, topic_index)

        end_time = datetime.now()
        print >> sys.stderr, 'Finishing time:', end_time
        print >> sys.stderr, 'It took', end_time - start_time,
        print >> sys.stderr, 'to import the analysis'

    cursor.execute('PRAGMA journal_mode=DELETE')
    cursor.execute('PRAGMA locking_mode=NORMAL')


#############################################################################
# Database creation code (in the order it's called in main)
#############################################################################

def create_analysis(name, readable_name, description):
    """Create the Analysis database object.
    """
    
    result = False
    print >> sys.stderr, 'Creating the analysis...  ',
    try:
        Analysis.objects.get(name=name, dataset=dataset)
        print >> sys.stderr, 'Analysis {n} already exists! Doing nothing...'.\
                format(n=name)
    except Analysis.DoesNotExist:
        a = Analysis(name=name, readable_name=readable_name,
                     description=description, dataset=dataset)
        a.save()
        result = True
        global analysis
        analysis = a
        try:
            os.mkdir('%s/%s-markup' % (dataset.dataset_dir, analysis.name))
        except OSError:
            print >> sys.stderr, 'The markup directory already exists.  ',
            print >> sys.stderr, 'Doing nothing...'
    print >> sys.stderr, 'Done'
    return result


@transaction.commit_manually
def create_topic_table(topics, topicinfo):
    num_per_dot = max(1, int(len(topics)/NUM_DOTS))
    print >> sys.stderr, 'Creating the Topic Table (%d topics per dot)' % (
            num_per_dot),
    sys.stdout.flush()
    start = datetime.now()
    num_so_far = 0
    topic_index = dict()
    for topic in topics:
        num_so_far += 1
        if num_so_far % num_per_dot == 0:
            print >> sys.stderr, '.',
            sys.stdout.flush()
        t = Topic(number=topic, analysis=analysis, name=topicinfo[topic][1],
                total_count=topicinfo[topic][0])
        t.save()
        topic_index[topic] = t
    transaction.commit()
    end = datetime.now()
    print >> sys.stderr, '  Done', end - start
    return topic_index


@transaction.commit_manually
def create_doctopic_table(doctopic, doc_index, topic_index):
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
def create_topicword_table(topicword, topic_index, word_index):
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
def create_doctopicword_table(doctopicword, doc_index, topic_index, word_index):
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
def create_attrvaltopic_table(attrvaltopic, attr_index, val_index, topic_index):
    num_per_dot = max(1, int(len(attrvaltopic)/NUM_DOTS))
    print >> sys.stderr, 'Creating the AttributeValueTopic Table',
    print >> sys.stderr, '(%d entries per dot)' % (num_per_dot),
    sys.stdout.flush()
    start = datetime.now()
    num_so_far = 0
    for attribute, value, topic in attrvaltopic:
        num_so_far += 1
        if num_so_far % num_per_dot == 0:
            print >> sys.stderr, '.',
            sys.stdout.flush()
        attr = attr_index[attribute]
        val = val_index[(value, attribute)]
        t = topic_index[topic]
        count = attrvaltopic[(attribute, value, topic)]
        avt = AttributeValueTopic(attribute=attr, value=val, topic=t,
                count=count)
        avt.save()
    transaction.commit()
    end = datetime.now()
    print >> sys.stderr, '  Done', end - start


#############################################################################
# Parsing and other intermediate code (not directly modifying the database)
#############################################################################

def parse_attributes(attribute_file):
    """
    Parse the contents of the attributes file, which should
    consist of a JSON formatted text file with the following
    format: [ {'path': <path>, 'attributes':{'attribute': 'value',...}}, ...] 
    """
    print >> sys.stderr, 'Parsing the JSON attributes file...',
    sys.stdout.flush()
    start = datetime.now()
    file_data = open(attribute_file).read()
    parsed_data = anyjson.deserialize(file_data)
    del file_data
    count = 0
    attribute_table = {}
    documents = set()
    attributes = set()
    values = defaultdict(set)
    for document in parsed_data:
        count += 1
        if count % 50000 == 0:
            print >> sys.stderr, count
            sys.stdout.flush()
        attribute_values = document['attributes']
        filename = document['path']
        documents.add(filename)
        attribute_table[filename] = attribute_values
        for attribute in attribute_values:
            attributes.add(attribute)
            value = attribute_values[attribute]
            if isinstance(value, basestring):
                values_set = [value]
            else:
                values_set = value
            for value in values_set:
                values[attribute].add(value)
    end = datetime.now()
    print >> sys.stderr, '  Done', end - start
    print >> sys.stderr, 'Populating the indexes for faster lookups...',
    start = datetime.now()
    sys.stdout.flush()
    doc_index = dict()
    attr_index = dict()
    value_index = dict()
    for doc in dataset.document_set.all():
        doc_index[doc.filename] = doc
    for attr in dataset.attribute_set.all():
        attr_index[attr.name] = attr
        for val in attr.value_set.all():
            value_index[(val.value, attr.name)] = val
    end = datetime.now()
    print >> sys.stderr, '  Done', end - start
    return doc_index, attr_index, value_index, attribute_table


@transaction.commit_manually
def parse_mallet_file(state_file, attribute_table, tokenized_file, files_dir, token_regex):
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
    topics = set()
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
                    markup_state.output_file()
                markup_state.initialize(files_dir, docpath)
            markup_state.markup_stop_words(word)
            markup_state.markup_word(word, topic)
            # Now other database stuff
            topics.add(topic)
            words.add(word)
            doctopic[(docpath, topic)] += 1
            topicword[(topic, word)] += 1
            doctopicword[(docpath, topic, word)] += 1
            for attr in attribute_table[docpath]:
                value = attribute_table[docpath][attr]
                if isinstance(value, basestring):
                    values_set = [value]
                else:
                    values_set = value
                for value in values_set:
                    attrvaltopic[(attr, value, topic)] += 1
    markup_state.markup_stop_words()
    markup_state.output_file()
    f.close()
    transaction.commit()

    end = datetime.now()
    print >> sys.stderr, '  Done', end - start
    print >> sys.stderr, 'Populating the word index...',
    start = datetime.now()
    sys.stdout.flush()
    word_index = dict()
    for word in dataset.word_set.all():
        word_index[word.type] = word
    end = datetime.now()
    print >> sys.stderr, '  Done', end - start
    sys.stdout.flush()
    return doctopic, topicword, doctopicword, attrvaltopic, topics, word_index


def create_topic_info(topicword):
    """Create a mapping from topic to total count and name using topicword

    Total count is the total number of tokens in the entire analysis that had
    that topic.  The name is generated however you wish.  We currently just
    take the top two words and separate them by a space.
    """

    totalcounts = defaultdict(int)
    wordcounts = defaultdict(list)

    for topic, word in topicword:
        count = topicword[(topic, word)]
        totalcounts[topic] += count
        wordcounts[topic].append((count, word))

    topicinfo = dict()
    for topic in totalcounts:
        top_words = wordcounts[topic]
        top_words.sort()
        top_words.reverse()
        name = ' '.join([x[1] for x in top_words][:2])
        topicinfo[topic] = (totalcounts[topic], name)

    return topicinfo


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

    def output_file(self):
        markup_file_name = '%s-markup/' % analysis.name
        markup_file_name += self.path
        file = create_dirs_and_open(dataset.dataset_dir + '/' + markup_file_name)
        file.write(anyjson.serialize(self.markup))
        document = Document.objects.get(filename=self.path)
        markup_file = MarkupFile(document=document, analysis=analysis,
                path=markup_file_name)
        markup_file.save()


# vim: et sw=4 sts=4
