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

from import_scripts.metadata import Metadata

from topic_modeling.visualize.models import WordToken, WordType
from topic_modeling.visualize.models import Dataset
from topic_modeling.visualize.models import Document

from django.db import connection, transaction

from datetime import datetime
from topic_modeling import settings

NUM_DOTS = 100

def import_dataset(name, readable_name, description, metadata_filenames,
                   dataset_dir, files_dir, token_regex):
    
    print >> sys.stderr, "dataset_import({0})".format(
        ', '.join([name, readable_name, description,
        metadata_filenames['datasets'], metadata_filenames['documents'], metadata_filenames['word_types'], metadata_filenames['word_tokens'],
        dataset_dir, files_dir]))
    
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
        document_metadata = Metadata(metadata_filenames['documents'])
        
        if settings.database_type()=='sqlite3':
            cursor = connection.cursor()
            cursor.execute('PRAGMA journal_mode=DELETE')
            cursor.execute('PRAGMA locking_mode=NORMAL')
        end_time = datetime.now()
        print >> sys.stderr, 'Finishing time:', end_time
        print >> sys.stderr, 'It took', end_time - start_time,
        print >> sys.stderr, 'to import the dataset'

@transaction.commit_manually
def _load_documents(dataset, token_regex):
    print >> sys.stderr, 'Loading documents...  ',
    for (dirpath, _dirnames, filenames) in os.walk(dataset.files_dir):
        for filename in filenames:
            filename = '%s/%s' % (dirpath, filename)
            doc, _ = Document.objects.get_or_create(dataset=dataset, filename=filename)
            print >> sys.stderr, filename
            
            file = open(filename)
            content = file.read()
            file.close()
            del file
            
            for token_index,match in enumerate(re.finditer(token_regex, content)):
                token = match.group()
                token_lc = token.lower()
                type, type_created = WordType.objects.get_or_create(type=token_lc)
                if type_created: transaction.commit()
                WordToken.objects.create(type=type, doc=doc, token_index=token_index, start=match.start())
            del content
            transaction.commit()

#############################################################################
# Database creation code (in the order it's called in main)
#############################################################################

def _create_dataset(name, readable_name, description, dataset_dir, files_dir):
    print >> sys.stderr, 'Creating the dataset...  ',
    dataset,created = Dataset.objects.get_or_create(name=name, readable_name=readable_name, description=description,
                    dataset_dir=dataset_dir, files_dir=files_dir)
    print >> sys.stderr, 'Done'
    return dataset,created

# vim: et sw=4 sts=4
