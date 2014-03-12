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

from topic_modeling.visualize.models import WordToken, WordType, WordTokenMetricValue
from topic_modeling.visualize.models import Dataset
from topic_modeling.visualize.models import Document
from topic_modeling.tools import TimeLongThing

from django.db import connection, connections, transaction
from django.db.models import Max
from django.db.utils import DatabaseError

from datetime import datetime
from topic_modeling import settings
import logging

logger = logging.getLogger('root')

def create_dataset_db_entry(database_id, dataset_id, readable_name, description, dataset_dir, files_dir):
    '''\
    Creates the database entry for the specified dataset.
    Returns the Dataset object.
    '''
    if Dataset.objects.using(database_id).filter(name=dataset_id).exists():
        return
    
    dataset_db, created = Dataset.objects.using(database_id).get_or_create(name=dataset_id, readable_name=readable_name, description=description,
                                            dataset_dir=dataset_dir, files_dir=files_dir)
    return dataset_db



def import_documents_into_database(database_id, dataset_identifier, documents):
    '''\
    Creates database entries for each document.
    '''
    dataset = Dataset.objects.using(database_id).get(name=dataset_identifier)
    
    # check to see if they exists already
    if dataset.documents.exists():
        return
    
    try: # create the document entries
        primary_key = 0
        if Document.objects.using(database_id).all().exists():
            primary_key = Document.objects.using(database_id).all().aggregate(Max('id'))['id__max'] + 1
        documents_to_create = []
        for doc_id, doc_path in documents.items():
            doc = Document(id=primary_key, dataset=dataset, filename=doc_id, full_path=doc_path)
            primary_key += 1
            documents_to_create.append(doc)
        Document.objects.using(database_id).bulk_create(documents_to_create)
    except Exception as e: # remove documents if there is an error
        try:
            dataset.documents.delete()
        except:
            pass
        raise e

def check_documents_for_tokens(database_id, dataset_identifier):
    '''\
    Checks each document for tokens.
    Returns false if any document does not have tokens.
    '''
    dataset = Dataset.objects.using(database_id).get(name=dataset_identifier)
    for document in dataset.documents.all():
        if not document.tokens.exists():
            logger.warn('Dataset present, but not all documents are populated: %s %d' % (document.filename, document.pk))
            return False
    return True

# TODO insert custom code to make sqlite even faster
# TODO handle error case, remove items from database
def import_document_word_tokens(database_id, dataset_identifier, words):
    '''\
    This imports the different words, their indexes and their start location into the database.
    words is a dictionary where the key identifies the document and the 
    '''
    if check_documents_for_tokens(database_id, dataset_identifier):
        return
    
    dataset = Dataset.objects.using(database_id).get(name=dataset_identifier)
    
    
    
    # get all word types currently in the database
    word_types = dict((wtype.type, wtype) for wtype in WordType.objects.using(database_id).all())
    
    # pk = primary key
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
    for doc_id in words:
        doc = document_query.get(filename=doc_id)
        
        # import every word in the document
        for word, index, start_pos in words[doc_id]:
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
    WordType.objects.using(database_id).bulk_create(word_types_to_create)
    WordToken.objects.using(database_id).bulk_create(word_tokens_to_create)



# vim: et sw=4 sts=4
