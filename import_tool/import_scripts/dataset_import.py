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


import os, sys
import re

from topic_modeling.visualize.models import WordToken, WordType, WordTokenMetricValue
from topic_modeling.visualize.models import Dataset
from topic_modeling.visualize.models import Document
from topic_modeling.tools import TimeLongThing

from django.db import connection, transaction
from django.db.utils import DatabaseError

from datetime import datetime
from topic_modeling import settings
import logging

logger = logging.getLogger('root')

def check_dataset(name):
    try:
        dataset = Dataset.objects.get(name=name)
    except (Dataset.DoesNotExist, DatabaseError):
        return False
    if not dataset.documents.count():
        return False
    for document in dataset.documents.all():
        if not document.tokens.count():
            logger.warn('Dataset present, but not all documents are populated: %s %d' % (document.filename, document.pk))
            return False

def import_dataset(name, readable_name, description, metadata_filenames,
                   dataset_dir, files_dir, token_regex, dont_overwrite=False):
    '''Import the dataset into the Database

    !! This will overwrite existing datasets unless dont_overwrite is True

    1) create a Dataset object
    2) create WorkType objects for each unique word in the entire directory
    @todo: we iterate through all the words *twice*, once to make wordtypes,
            and again to make the wordtokens!
    3) create Document objects for each file in the dataset directory
    4) create WordToken objects for each "word" (found by c['token_regex'])

    '''

    print >> sys.stderr, "dataset_import({0})".format(', '.join(
        [name, readable_name, description,
         metadata_filenames['datasets'], metadata_filenames['documents'],
         metadata_filenames['word_types'], metadata_filenames['word_tokens'],
         dataset_dir, files_dir]
    ))

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

    dataset, created = _create_dataset(name, readable_name, description, dataset_dir, files_dir)
    if not dont_overwrite or created:
        _load_documents(dataset, token_regex)

        if settings.database_type()=='sqlite3':
            cursor = connection.cursor()
            cursor.execute('PRAGMA journal_mode=DELETE')
            cursor.execute('PRAGMA locking_mode=NORMAL')
        end_time = datetime.now()
        print >> sys.stderr, 'Finishing time:', end_time
        print >> sys.stderr, 'It took', end_time - start_time,
        print >> sys.stderr, 'to import the dataset'
    else:
        print >> sys.stderr, 'Skipping', name, readable_name

def _create_documents(files_dir):
    pass

def _load_documents(dataset, token_regex):
    '''This goes through the dataset (by walking through the files in dataset.files_dir).

    1) creates word types
    2) creates documents
    3) creates word tokens
    '''
    if dataset.documents.all().count():
        logger.info('Deleting old documents')
        for document in dataset.documents.all():
            WordTokenMetricValue.objects.raw('delete from visualize_wordtokenmetricvalue wtv join visualize_wordtoken wt on wtv.token_id=wt.id where wt.document_id=%s', [document.pk])
            WordToken.objects.raw('delete from visualize_wordtoken where document_id=%d' % document.pk)
            Document.objects.raw('delete from visualize_document where id=%s', [document.pk])
        # dataset.documents.all().delete()

    logger.info('Creating the Word Types')
    word_types = _types(dataset.files_dir, token_regex)

    print >> sys.stderr, 'Creating documents and tokens...  '

    all_files = []

    for (dirpath, _dirnames, filenames) in os.walk(dataset.files_dir):
        for filename in filenames:
            all_files.append([dataset.files_dir, filename, os.path.join(dirpath, filename)])
    all_files.sort()

    timer = TimeLongThing(len(all_files), .01, .1)
    for i, (dirpath, filename, full_path) in enumerate(all_files):
        full_filename = os.path.join(dirpath, filename)
        doc, _ = Document.objects.get_or_create(dataset=dataset,
                filename=filename,
                full_path=full_filename)
        timer.inc()

        with open(full_filename) as r:
            content = r.read()

        tokens = []
        for position, match in enumerate(re.finditer(token_regex, content)):
            token = match.group()
            token_lc = token.lower()
            if token_lc not in word_types:
                raise Exception('New word type found: %s in document %s %d' % (token_lc,
                    full_filename, doc.pk))
            word_type = word_types[token_lc]
            tokens.append(WordToken(type=word_type, document=doc,
                    token_index=position, start=match.start()))
        WordToken.objects.bulk_create(tokens)
        del content
        '''
        if not doc.tokens.all().count():
            raise Exception('Failed to import word tokens for %s %d'
                    % (full_filename, doc.pk))
        '''

def _types(files_dir, token_regex):
    print >> sys.stderr, 'Ensuring word types...  '
    type_objs = dict((wtype.type, wtype) for wtype in WordType.objects.all())

    types_in_dataset = set(wtype for _filename, _token_idx, wtype
            in _token_iterator(files_dir, token_regex))

    types_dict = {}
    for wtype in types_in_dataset:
        if wtype in type_objs:
            types_dict[wtype] = type_objs[wtype]
        else:
            types_dict[wtype] = WordType.objects.create(type=wtype)

    return types_dict

def _token_iterator(files_dir, token_regex):
    for (dirpath, _dirnames, filenames) in os.walk(files_dir):
        for filename in filenames:
            full_filename = '%s/%s' % (dirpath, filename)

            with open(full_filename) as r:
                content = r.read()

            for token_idx,match in enumerate(re.finditer(token_regex, content)):
                token = match.group()
                token_lc = token.lower()
                yield filename, token_idx, token_lc

def _create_dataset(name, readable_name, description, dataset_dir, files_dir):
    print >> sys.stderr, 'Creating the dataset...  ',
    dataset,created = Dataset.objects.get_or_create(name=name, readable_name=readable_name, description=description,
                    dataset_dir=dataset_dir, files_dir=files_dir)
    print >> sys.stderr, 'Done'
    return dataset, created

# vim: et sw=4 sts=4
