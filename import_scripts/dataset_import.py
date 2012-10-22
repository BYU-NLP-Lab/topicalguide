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

from topic_modeling.visualize.models import WordToken, WordType
from topic_modeling.visualize.models import Dataset
from topic_modeling.visualize.models import Document

from django.db import connection, transaction

from datetime import datetime
from topic_modeling import settings

def import_dataset(name, readable_name, description, metadata_filenames,
                   dataset_dir, files_dir, token_regex):
    '''Import the dataset into the Database

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
    if created:
        _load_documents(dataset, token_regex)

        if settings.database_type()=='sqlite3':
            cursor = connection.cursor()
            cursor.execute('PRAGMA journal_mode=DELETE')
            cursor.execute('PRAGMA locking_mode=NORMAL')
        end_time = datetime.now()
        print >> sys.stderr, 'Finishing time:', end_time
        print >> sys.stderr, 'It took', end_time - start_time,
        print >> sys.stderr, 'to import the dataset'

def _create_documents(files_dir):
    pass

@transaction.commit_manually
def _load_documents(dataset, token_regex):
    word_types = _types(dataset.files_dir, token_regex)

    print >> sys.stderr, 'Creating documents and tokens...  ',

    try:
        all_files = []
        for (dirpath, _dirnames, filenames) in os.walk(dataset.files_dir):
            for filename in filenames:
                all_files.append([dirpath, filename])
        for i, (dirpath, filename) in enumerate(all_files):
            full_filename = '%s/%s' % (dirpath, filename)
            doc, _ = Document.objects.get_or_create(dataset=dataset, filename=filename)
            if i % 10 == 0:
                print>>sys.stderr, ".",
                sys.stderr.flush()
            if i % 100 == 0:
                print >> sys.stderr, "%d%% done (%d of %d)" % (i*100//len(all_files),
                        i, len(all_files))

            with open(full_filename) as r:
                content = r.read()

            for position,match in enumerate(re.finditer(token_regex, content)):
                token = match.group()
                token_lc = token.lower()
                try:
                    word_type = word_types[token_lc]
                except KeyError:
                    word_type, type_created = WordType.objects.get_or_create(type=token_lc)
                    if type_created: transaction.commit()
                    word_types[token_lc] = word_type
                WordToken.objects.create(type=word_type, document=doc,
                        token_index=position, start=match.start())
            del content
            transaction.commit()
    except:
        transaction.rollback()
        raise

def _types(files_dir, token_regex):
    print >> sys.stderr, 'Ensuring word types...  ',
    type_objs = dict((wtype.type, wtype) for wtype in WordType.objects.all())

    types_in_dataset = set(wtype for _filename, _token_idx, wtype in _token_iterator(files_dir, token_regex))
    types_to_create = types_in_dataset.difference(type_objs.keys())

    types_dict = type_objs.fromkeys(types_in_dataset)
    for wtype in types_to_create:
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
