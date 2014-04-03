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
from __future__ import print_function

import os, sys
import re
import logging

from topic_modeling.visualize.models import WordToken, WordType, WordTokenMetricValue
from topic_modeling.visualize.models import Dataset
from topic_modeling.visualize.models import Document
from topic_modeling.tools import TimeLongThing

from django.db import connection, connections, transaction
from django.db.models import Max
from django.db.utils import DatabaseError

from datetime import datetime
from topic_modeling import settings
from topic_modeling.tools import TimeLongThing


logger = logging.getLogger('root')


def create_dataset_db_entry(database_id, dataset, dataset_dir, files_dir):
    """
    Create the database entry for the specified dataset.
    Return the Dataset object.
    """
    if Dataset.objects.using(database_id).filter(name=dataset.get_identifier()).exists():
        return Dataset.objects.using(database_id).get(name=dataset.get_identifier())
    else:
        dataset_db = None
        with transaction.commit_on_success():
            dataset_db = Dataset.objects.using(database_id)\
                                .create(name=dataset.get_identifier(), 
                                        readable_name=dataset.get_readable_name(), 
                                        description=dataset.get_description(),
                                        dataset_dir=dataset_dir, 
                                        files_dir=files_dir)
        return dataset_db
    


def import_documents_into_database(database_id, dataset_identifier, documents):
    """Create database entries for each document."""
    dataset = Dataset.objects.using(database_id).get(name=dataset_identifier)
    
    # check to see if they exist already
    if dataset.documents.exists():
        return
    
    # create the document entries
    with transaction.commit_on_success():
        # get unique primary key
        primary_key = 0
        if Document.objects.using(database_id).all().exists():
            primary_key = Document.objects.using(database_id).all().aggregate(Max('id'))['id__max'] + 1
        # create Document objects
        documents_to_create = []
        for doc_id, doc_path in documents.items():
            doc = Document(id=primary_key, dataset=dataset, filename=doc_id, full_path=doc_path)
            primary_key += 1
            documents_to_create.append(doc)
        # create objects in database
        Document.objects.using(database_id).bulk_create(documents_to_create)


def check_documents_for_tokens(database_id, dataset_identifier):
    """
    Check each document for tokens.
    Return false if any document does not have tokens.
    """
    dataset = Dataset.objects.using(database_id).get(name=dataset_identifier)
    for document in dataset.documents.all():
        if not document.tokens.exists():
            logger.warn('Dataset present, but not all documents are populated: %s %d' % (document.filename, document.pk))
            return False
    return True

def import_document_word_tokens(database_id, dataset_identifier, words):
    """
    Import the different words, their indexes and their start location into the database.
    words is a dictionary where the key identifies the document and the value is a 
    list of tuples like: (word, index, start_position)
    """
    if check_documents_for_tokens(database_id, dataset_identifier):
        return
    
    dataset = Dataset.objects.using(database_id).get(name=dataset_identifier)
    
    # get all word types currently in the database
    word_types = dict((wtype.type, wtype) for wtype in WordType.objects.using(database_id).all())
    
    # set up the timer
    total_words = 0
    for doc_id in words:
        total_words += len(words[doc_id])
    timer = TimeLongThing(total_words, 0, 0)
    
    # pk is primary key
    word_type_pk = 0
    if WordType.objects.using(database_id).all().exists():
        word_type_pk = WordType.objects.using(database_id).all().aggregate(Max('id'))['id__max'] + 1
    word_token_pk = 0
    if WordToken.objects.using(database_id).all().exists():
        word_token_pk = WordToken.objects.using(database_id).all().aggregate(Max('id'))['id__max'] + 1
    
    document_query = Document.objects.using(database_id).all()
    document_query.count() # load documents into memory
    word_types_to_create = []
    word_tokens_to_create = []
    print('  Creating WordTokens...')
    with transaction.commit_on_success():
        for doc_id in words:
            doc = document_query.get(filename=doc_id)
            
            # import every word in the document
            for word, index, start_pos in words[doc_id]:
                timer.inc()
                word_type = None
                if not word in word_types: # create the word type if it doesn't exist
                    word_type = WordType(id=word_type_pk, type=word)
                    word_types[word] = word_type
                    word_type_pk += 1
                    word_types_to_create.append(word_type)
                else:
                    word_type = word_types[word]
                word_token = WordToken(id=word_token_pk, type=word_type, document_id=doc.id,
                                       token_index=index, start=start_pos)
                word_token_pk += 1
                word_tokens_to_create.append(word_token)
        print('  Committing WordTokens to database...')
        WordType.objects.using(database_id).bulk_create(word_types_to_create)
        WordToken.objects.using(database_id).bulk_create(word_tokens_to_create)



# vim: et sw=4 sts=4
