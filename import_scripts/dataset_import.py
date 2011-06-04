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


import os, sys
import time

sys.path.append(os.curdir)
os.environ['DJANGO_SETTINGS_MODULE'] = 'topic_modeling.settings'

from topic_modeling import settings
settings.DEBUG = False


from topic_modeling.visualize.models import Attribute, DatasetMetaInfo,\
    DatasetMetaInfoValue
from topic_modeling.visualize.models import AttributeValue
from topic_modeling.visualize.models import AttributeValueDocument
from topic_modeling.visualize.models import AttributeValueWord
from topic_modeling.visualize.models import Dataset
from topic_modeling.visualize.models import Document
from topic_modeling.visualize.models import DocumentWord
from topic_modeling.visualize.models import Value
from topic_modeling.visualize.models import Word

from django.db import connection, transaction

from collections import defaultdict
from datetime import datetime

import topic_modeling.anyjson as anyjson

# A couple of global variables just to make life easier, so I don't have to
# pass them around so much - they're created once and then never change
dataset = None

NUM_DOTS = 100

def import_dataset(name, readable_name, description, state_file,
        metadata_filenames,
        dataset_dir, files_dir):
    
    print >> sys.stderr, "dataset_import({0})".format(
        ', '.join([name, readable_name, description, state_file,
        metadata_filenames['datasets'], metadata_filenames['documents'], metadata_filenames['words'],
        dataset_dir, files_dir]))
    
    start_time = datetime.now()
    print >> sys.stderr, 'Starting time:', start_time
    # These are some attempts to make the database access a little faster
    cursor = connection.cursor()
    cursor.execute('PRAGMA temp_store=MEMORY')
    cursor.execute('PRAGMA synchronous=OFF')
    cursor.execute('PRAGMA cache_size=2000000')
    cursor.execute('PRAGMA journal_mode=MEMORY')
    cursor.execute('PRAGMA locking_mode=EXCLUSIVE')

    created = create_dataset(name, readable_name, description, dataset_dir, files_dir)
    if created:
        dataset_metadata = Metadata(metadata_filenames['datasets'])
        _import_dataset_metadata(dataset_metadata)
        
        document_metadata = Metadata(metadata_filenames['documents'])
        _import_document_metadata(document_metadata)
        
        word_metadata = Metadata(metadata_filenames['words'])
        _import_word_metadata(word_metadata)
        
        docs, attrs, vals, attrvaldoc = _import_document_attributes(document_metadata)

        doc_index = create_document_table(docs)
        attr_index = create_attribute_table(attrs)
        value_index = create_value_table(vals, attr_index)
        create_attrvaldoc_table(attrvaldoc, attr_index, value_index, doc_index)

        # BAD!  We currently rely on a Mallet output file in order to give us
        # counts for the database.  This should be fixed somehow.  The problem
        # is that it depends on stopword lists and other kinds of formating.
        words, docword, attrval, attrvalword = parse_mallet_file(state_file,
                document_metadata)
        word_index = create_word_table(words)
        create_docword_table(docword, doc_index, word_index)
        create_attrval_table(attrval, attr_index, value_index)
        create_attrvalword_table(attrvalword, attr_index, value_index,
                word_index)

        cursor.execute('PRAGMA journal_mode=DELETE')
        cursor.execute('PRAGMA locking_mode=NORMAL')
        end_time = datetime.now()
        print >> sys.stderr, 'Finishing time:', end_time
        print >> sys.stderr, 'It took', end_time - start_time,
        print >> sys.stderr, 'to import the dataset'



#############################################################################
# Database creation code (in the order it's called in main)
#############################################################################

def create_dataset(name, readable_name, description, dataset_dir, files_dir):
    print >> sys.stderr, 'Creating the dataset...  ',
    try:
        Dataset.objects.get(name=name)
        print >> sys.stderr, 'Dataset {n} already exists!  Doing nothing...'.\
                format(n=name)
        return False
    except Dataset.DoesNotExist:
        d = Dataset(name=name, readable_name=readable_name, description=description,
                    dataset_dir=dataset_dir, files_dir=files_dir)
        d.save()
        global dataset
        dataset = d
    print >> sys.stderr, 'Done'
    return True


@transaction.commit_manually
def create_document_table(filenames):
    num_per_dot = max(1, int(len(filenames)/NUM_DOTS))
    print >> sys.stderr, 'Creating the Document Table',
    print >> sys.stderr, '(%d documents per dot)' % (num_per_dot),
    sys.stdout.flush()
    start = datetime.now()
    num_so_far = 0
    doc_index = dict()
    for filename in filenames:
        num_so_far += 1
        if num_so_far % num_per_dot == 0:
            print >> sys.stderr, '.',
            sys.stdout.flush()
        doc = Document(filename=filename, dataset=dataset)
        doc.save()
        doc_index[filename] = doc
    transaction.commit()
    end = datetime.now()
    print >> sys.stderr, '  Done', end - start
    return doc_index


@transaction.commit_manually
def create_attribute_table(attributes):
    num_per_dot = max(1, int(len(attributes)/NUM_DOTS))
    print >> sys.stderr, 'Creating the Attribute Table',
    print >> sys.stderr, '(%d attributes per dot)' % (num_per_dot),
    sys.stdout.flush()
    start = datetime.now()
    num_so_far = 0
    attr_index = dict()
    for attribute in attributes:
        num_so_far += 1
        if num_so_far % num_per_dot == 0:
            print >> sys.stderr, '.',
            sys.stdout.flush()
        attr = Attribute(name=attribute, dataset=dataset)
        attr.save()
        attr_index[attribute] = attr
    transaction.commit()
    end = datetime.now()
    print >> sys.stderr, '  Done', end - start
    return attr_index


@transaction.commit_manually
def create_value_table(values, attr_index):
    entries = []
    for attribute in values:
        entries.extend(values[attribute])
    num_per_dot = max(1, int(len(entries)/NUM_DOTS))
    print >> sys.stderr, 'Creating the Value Table',
    print >> sys.stderr, '(%d values per dot)' % (num_per_dot),
    sys.stdout.flush()
    start = datetime.now()
    num_so_far = 0
    value_index = dict()
    for attribute in values:
        for value in values[attribute]:
            num_so_far += 1
            if num_so_far % num_per_dot == 0:
                print >> sys.stderr, '.',
                sys.stdout.flush()
            val = Value(value=value, attribute=attr_index[attribute])
            val.save()
            value_index[(value, attribute)] = val
    transaction.commit()
    end = datetime.now()
    print >> sys.stderr, '  Done', end - start
    return value_index


@transaction.commit_manually
def create_attrvaldoc_table(attrvaldoc, attr_index, value_index, doc_index):
    num_per_dot = max(1, int(len(attrvaldoc)/NUM_DOTS))
    print >> sys.stderr, 'Creating the AttributeValueDocument Table',
    print >> sys.stderr, '(%d entries per dot)' % (num_per_dot),
    sys.stdout.flush()
    start = datetime.now()
    num_so_far = 0
    for attribute, value, filename in attrvaldoc:
        num_so_far += 1
        if num_so_far % num_per_dot == 0:
            print >> sys.stderr, '.',
            sys.stdout.flush()
        doc = doc_index[filename]
        attr = attr_index[attribute]
        val = value_index[(value, attribute)]
        attrvaldoc = AttributeValueDocument(document=doc, attribute=attr,
                value=val)
        attrvaldoc.save()
    transaction.commit()
    end = datetime.now()
    print >> sys.stderr, '  Done', end - start


@transaction.commit_manually
def create_word_table(words):
    num_per_dot = max(1, int(len(words)/NUM_DOTS))
    print >> sys.stderr, 'Creating the Word Table',
    print >> sys.stderr, '(%d words per dot)' % (num_per_dot),
    sys.stdout.flush()
    start = datetime.now()
    num_so_far = 0
    word_index = dict()
    for word in words:
        num_so_far += 1
        if num_so_far % num_per_dot == 0:
            print >> sys.stderr, '.',
            sys.stdout.flush()
        count = words[word]
        if '_' in word:
            w = Word(dataset=dataset, type=word, ngram=True, count=count)
        else:
            w = Word(dataset=dataset, type=word, count=count)
        w.save()
        word_index[word] = w
    transaction.commit()
    end = datetime.now()
    print >> sys.stderr, '  Done', end - start
    return word_index


@transaction.commit_manually
def create_docword_table(docword, doc_index, word_index):
    num_per_dot = max(1, int(len(docword)/NUM_DOTS))
    print >> sys.stderr, 'Creating the DocumentWord table',
    print >> sys.stderr, '(%d entries per dot)' % (num_per_dot),
    sys.stdout.flush()
    num_so_far = 0
    start = datetime.now()
    total_doc_counts = defaultdict(int)
    for filename, word in docword:
        num_so_far += 1
        if num_so_far % num_per_dot == 0:
            print >> sys.stderr, '.',
            sys.stdout.flush()
        doc = doc_index[filename]
        w = word_index[word]
        count = docword[(filename, word)]
        dw = DocumentWord(document=doc, word=w, count=count)
        dw.save()
        total_doc_counts[filename] += count
    transaction.commit()
    end = datetime.now()
    print >> sys.stderr, '  Done', end-start
    print >> sys.stderr, 'Updating Document total word counts...  ',
    for filename in total_doc_counts:
        doc = doc_index[filename]
        doc.word_count = total_doc_counts[filename]
        doc.save()
    transaction.commit()
    print >> sys.stderr, 'Done'


@transaction.commit_manually
def create_attrval_table(attrval, attr_index, value_index):
    num_per_dot = max(1, int(len(attrval)/NUM_DOTS))
    print >> sys.stderr, 'Creating the AttributeValue Table',
    print >> sys.stderr, '(%d entries per dot)' % (num_per_dot),
    sys.stdout.flush()
    start = datetime.now()
    num_so_far = 0
    for attribute, value in attrval:
        num_so_far += 1
        if num_so_far % num_per_dot == 0:
            print >> sys.stderr, '.',
            sys.stdout.flush()
        attr = attr_index[attribute]
        val = value_index[(value, attribute)]
        count = attrval[(attribute, value)]
        av = AttributeValue(attribute=attr, value=val, token_count=count)
        av.save()
    transaction.commit()
    end = datetime.now()
    print >> sys.stderr, '  Done', end - start


@transaction.commit_manually
def create_attrvalword_table(attrvalword, attr_index, value_index, word_index):
    num_per_dot = max(1, int(len(attrvalword)/NUM_DOTS))
    print >> sys.stderr, 'Creating the AttributeValueWord Table',
    print >> sys.stderr, '(%d entries per dot)' % (num_per_dot),
    sys.stdout.flush()
    start = datetime.now()
    num_so_far = 0
    for attribute, value, word in attrvalword:
        num_so_far += 1
        if num_so_far % num_per_dot == 0:
            print >> sys.stderr, '.',
            sys.stdout.flush()
        attr = attr_index[attribute]
        val = value_index[(value, attribute)]
        w = word_index[word]
        count = attrvalword[(attribute, value, word)]
        avw = AttributeValueWord(attribute=attr, value=val, word=w, count=count)
        avw.save()
    transaction.commit()
    end = datetime.now()
    print >> sys.stderr, '  Done', end - start


#############################################################################
# Parsing and other intermediate code (not directly modifying the database)
#############################################################################

def _import_document_attributes(document_metadata):
    """
    Parse the contents of the attributes file, which should
    consist of a JSON formatted text file with the following
    format: [ {'path': <path>, 'attributes':{'attribute': 'value',...}}, ...]
    """
    print >> sys.stderr, 'Importing document attributes (old-style metadata)...  ',
    sys.stdout.flush()
    start = datetime.now()
    count = 0
#    attribute_table = {}
    documents = set()
    attributes = set()
    values = defaultdict(set)
    attrvaldoc = set()
    for document_name, metadata in document_metadata.items():
        count += 1
        if count % 50000 == 0:
            print >> sys.stderr, count
            sys.stdout.flush()
#        attribute_values = document['attributes']
#        filename = document['path']
        documents.add(document_name)
#        attribute_table[document_name] = attribute_values
        for attribute,value in metadata.items():
            value = str(value)#Because Attribute only handles string types
            attributes.add(attribute)
            if isinstance(value, basestring):
                values_set = [value]
            else:
                values_set = value
            for value in values_set:
                values[attribute].add(value)
                attrvaldoc.add((attribute, value, document_name))
    print >> sys.stderr, 'Done'
    end = datetime.now()
    print >> sys.stderr, '  Done', end - start
    sys.stdout.flush()
    return documents, attributes, values, attrvaldoc


def parse_mallet_file(state_file, document_metadata):
    """ Parses the state output file from mallet

    That file lists individual tokens one per line in the following format:

    <document idx> <document path> <token idx> <type idx> <type> <topic>

    The state file is output from MALLET in a gzipped format.  This method
    assumes that the file has already been un-compressed.
    """
    print >> sys.stderr, 'Parsing the mallet file...  ',
    sys.stdout.flush()
    start = datetime.now()
    words = defaultdict(int)
    docword = defaultdict(int)
    attrvalue = defaultdict(int)
    attrvalueword = defaultdict(int)

    f = open(state_file)
    count = 0
    for line in f:
        count += 1
        if count % 100000 == 0:
            print >> sys.stderr, count
        line = line.strip()
        if line[0] != "#":
            _, docpath, __, ___, word, ____ = line.split()
            words[word] += 1
            docword[(docpath, word)] += 1
            for attr,value in document_metadata[docpath].items():
                value = str(value)#FIXME This conversion is for backwards compatibility with Attribute
                if isinstance(value, basestring):
                    values_set = [value]
                else:
                    values_set = value
                for value in values_set:
                    attrvalue[(attr, value)] += 1
                    attrvalueword[(attr, value, word)] += 1
    f.close()

    end = datetime.now()
    print >> sys.stderr, '  Done', end - start
    sys.stdout.flush()
    return words, docword, attrvalue, attrvalueword

#def _load_metadata(entity_type, attribute_types, filenames):
#    return Metadata(attribute_types[entity_type], filenames[entity_type])

def _import_dataset_metadata(dataset_metadata):
    print >> sys.stderr, 'Importing dataset metadata...  ',
    sys.stdout.flush()
    start = datetime.now()
    
    for dataset_name, metadata in dataset_metadata.items():
        dataset, _ = Dataset.objects.get_or_create(name=dataset_name)
        for attribute, value in metadata.items():
            mi,__ = DatasetMetaInfo.objects.get_or_create(name=attribute)
            miv, ___ = DatasetMetaInfoValue.objects.get_or_create(info_type=mi, dataset=dataset)
            miv.set(value)
            miv.save()
    end = datetime.now()
    print >> sys.stderr, '  Done', end - start

def _import_document_metadata(document_metadata):
    print >> sys.stderr, 'Importing document metadata...  ',
    sys.stdout.flush()
    start = datetime.now()
    
    for dataset_name, metadata in dataset_metadata.items():
        dataset, _ = Dataset.objects.get_or_create(name=dataset_name)
        for attribute, value in metadata.items():
            mi,__ = DatasetMetaInfo.objects.get_or_create(name=attribute)
            miv, ___ = DatasetMetaInfoValue.objects.get_or_create(info_type=mi, dataset=dataset)
            miv.set(value)
            miv.save()
    end = datetime.now()
    print >> sys.stderr, '  Done', end - start

def _import_word_metadata(word_metadata):
    print >> sys.stderr, 'Importing word metadata...  ',
    sys.stdout.flush()
    start = datetime.now()
    
    for dataset_name, metadata in dataset_metadata.items():
        dataset, _ = Dataset.objects.get_or_create(name=dataset_name)
        for attribute, value in metadata.items():
            mi,__ = DatasetMetaInfo.objects.get_or_create(name=attribute)
            miv, ___ = DatasetMetaInfoValue.objects.get_or_create(info_type=mi, dataset=dataset)
            miv.set(value)
            miv.save()
    end = datetime.now()
    print >> sys.stderr, '  Done', end - start

class MetadataWrapper(dict):
    def __init__(self, types, copy=None):
        self.types = types
        if copy:
            self.update(copy)
    
    def _get_super_item(self, key):
        return super(MetadataWrapper, self).__getitem__(key)
    
    def __getitem__(self, key):
        value = self._get_super_item(key)
        if isinstance(value, MetadataWrapper):
            return value
        elif isinstance(value, dict):
            value = MetadataWrapper(self.types, copy=value)
            self[key] = value
            return value
        return self._parse_type(self.types[key], value)
    
    def _parse_type(self, type, value):
        if type=='float':
            return float(value)
        elif type=='text':
            return str(value)
        elif type=='int':
            return int(value)
        elif type=='bool':
            return bool(value)
        elif type=='datetime':
            #Example: "2004-06-03T00:44:35"
            return time.strptime(str(value), "%Y-%m-%dT%H:%M:%S")
        else:
            raise Exception("Type '{0}' is not recognized.".format(type))
    
    def items(self):
        for key in self:
            value = self[key]
            yield key, value

class Metadata(MetadataWrapper):
    def __init__(self, filename):
        if not os.path.exists(filename):
            self.types = {}
        else:
            json_obj = anyjson.deserialize(open(filename).read())
            self.types = json_obj['types']
            self.update(json_obj['data'])

# vim: et sw=4 sts=4
