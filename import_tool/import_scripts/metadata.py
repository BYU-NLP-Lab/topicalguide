import os
import sys
import time

from datetime import datetime

from topic_modeling import anyjson
from topic_modeling.visualize.models import DatasetMetaInfo,\
    DatasetMetaInfoValue, Document, DocumentMetaInfo, DocumentMetaInfoValue,\
    AnalysisMetaInfo, AnalysisMetaInfoValue, TopicMetaInfo, TopicMetaInfoValue, WordType,\
    WordTypeMetaInfo, WordTypeMetaInfoValue, WordTokenMetaInfoValue, WordTokenMetaInfo
from django.db.models import Max
from topic_modeling.tools import TimeLongThing
import logging

logger = logging.getLogger('root')

datetime_format = "%Y-%m-%dT%H:%M:%S"

def import_dataset_metadata_into_database(database_id, dataset_db, dataset_metadata, dataset_metadata_types):
    '''\
    dataset_db The Dataset ORM object.
    dataset_metadata A dictionary with the metadata.
    dataset_metadata_types A dictionary specifying what type each metadatum is.
    
    Puts the metadata for the dataset into the database.
    '''
    # check to see if the dataset metadata is already in the database
    if DatasetMetaInfoValue.objects.using(database_id).filter(dataset=dataset_db).exists():
        return # if there is metadata then we're done here
    
    try: # try to put dataset metadata into database
        metadata = MetadataWrapper(dataset_metadata, dataset_metadata_types)
        
        meta_info_value_id = 0 # use this to assign primary keys for metadata values
        # check to see if there are other entries in the table, if so get the id of the most recently added
        if DatasetMetaInfoValue.objects.using(database_id).exists():
            meta_info_value_id = DatasetMetaInfoValue.objects.using(database_id).aggregate(Max('id'))['id__max'] + 1
        
        # create the objects
        meta_info_values = []
        for attribute, value in dataset_metadata.items():
            meta_info, __ = DatasetMetaInfo.objects.using(database_id).get_or_create(name=attribute)
            meta_info_value = DatasetMetaInfoValue(info_type=meta_info, dataset=dataset_db)
            meta_info_value.set(value)
            meta_info_value.id = meta_info_value_id
            meta_info_value_id += 1
            meta_info_values.append(meta_info_value)
        # put the objects into the database
        DatasetMetaInfoValue.objects.using(database_id).bulk_create(meta_info_values)
    except Exception as e: # if anything goes wrong try to clean-up the database
        try:
            DatasetMetaInfoValue.objects.using(database_id).filter(dataset=dataset_db).all().delete()
        except Exception:
            pass
        raise e

def import_document_metadata_into_database(database_id, dataset_db, document_metadata, document_metadata_types, timer=None):
    '''\
    Puts the document metadata into the database.
    '''
    # check to see if the document metadata is already in the database
    if dataset_db.documents.exists() and \
       dataset_db.documents.all()[0].metainfovalues.exists():
        return # if there is metadata then we're done here
    
    try: # try to put document metadata into database
        all_metadata = MetadataWrapper(document_metadata_types, document_metadata)
        
        meta_info_value_id = 0 # use this to assign primary keys for metadata values
        # check to see if there are other entries in the table, if so get the id of the most recently added
        if DocumentMetaInfoValue.objects.using(database_id).exists():
            meta_info_value_id = DocumentMetaInfoValue.objects.using(database_id).aggregate(Max('id'))['id__max'] + 1
        
        meta_info_values = []
        # create the objects
        for filename, metadata in all_metadata.iteritems():
            doc = Document.objects.using(database_id).get(dataset=dataset_db, filename=filename)
            for attribute, value in metadata.items():
                meta_info,__ = DocumentMetaInfo.objects.using(database_id).get_or_create(name=attribute)
                meta_info_value = DocumentMetaInfoValue(info_type=meta_info, document=doc)
                meta_info_value.set(value)
                meta_info_value.id = meta_info_value_id
                meta_info_value_id += 1
                meta_info_values.append(meta_info_value)
        # put the objects into the database
        DocumentMetaInfoValue.objects.using(database_id).bulk_create(meta_info_values)
    except Exception as e: # if anything goes wrong try to clean-up the database
        try:
            for document in dataset_db.documents.all():
                document.metainfovalues.all().delete()
        except Exception:
            pass
        raise e

def import_word_type_metadata(dataset, word_type_metadata):
    logger.info('Importing word type metadata...  ')
    sys.stdout.flush()
    start = datetime.now()

    for word_type, metadata in word_type_metadata.items():
        word, _ = WordType.objects.get_or_create(dataset=dataset, type=word_type)
        for attribute, value in metadata.items():
            mi,__ = WordTypeMetaInfo.objects.get_or_create(name=attribute)
            miv, ___ = WordTypeMetaInfoValue.objects.get_or_create(info_type=mi, word=word)
            miv.set(value)
            miv.save()
    end = datetime.now()
    logger.info('  Done %s' % (end - start))

def import_word_token_metadata(dataset, word_token_metadata):
    logger.info('Importing word token metadata...  ')
    sys.stdout.flush()
    start = datetime.now()

    for word_type, metadata in word_token_metadata.items():
        word_token, _ = dataset.tokens.get_or_create(type__type=word_type)
        for attribute, value in metadata.items():
            mi,__ = WordTokenMetaInfo.objects.get_or_create(name=attribute)
            miv, ___ = WordTokenMetaInfoValue.objects.get_or_create(info_type=mi, word_token=word_token)
            miv.set(value)
            miv.save()
    end = datetime.now()
    logger.info('  Done %s' % (end - start))

def import_analysis_metadata(analysis, analysis_metadata):
    logger.info('Importing analysis metadata...  ')
    sys.stdout.flush()
    start = datetime.now()

    if analysis.name in analysis_metadata:
        for attribute, value in analysis_metadata[analysis.name].items():
            mi,__ = AnalysisMetaInfo.objects.get_or_create(name=attribute)
            miv, ___ = AnalysisMetaInfoValue.objects.get_or_create(info_type=mi, analysis=analysis)
            miv.set(value)
            miv.save()

    end = datetime.now()
    logger.info('  Done %s' % (end - start))

def import_topic_metadata(analysis, topic_metadata):
    logger.info('Importing topic metadata...  ')
    sys.stdout.flush()
    start = datetime.now()

    for topic in analysis.topics.all():
        topic_num = unicode(topic.number)
        if topic_num in topic_metadata:
            metadata = topic_metadata[topic_num]
            for attribute, value in metadata.items():
                mi,__ = TopicMetaInfo.objects.get_or_create(name=attribute)
                miv, ___ = TopicMetaInfoValue.objects.get_or_create(info_type=mi, topic=topic)
                miv.set(value)
                miv.save()

    end = datetime.now()
    logger.info('  Done %s' % (end - start))

class MetadataWrapper(dict):
    def __init__(self, types, data=None):
        self.types = types
        if data:
            self.update(data)

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

    def _parse_type(self, type_, value):
        if type_=='float':
            return float(value)
        elif type_=='text':
            return unicode(value)
        elif type_=='int':
            return int(value)
        elif type_=='bool':
            return bool(value)
        elif type_=='datetime':
            #Example: "2004-06-03T00:44:35"
            return time.strptime(unicode(value), datetime_format)
        else:
            raise Exception("Type '{0}' is not recognized.".format(type_))

    def items(self):
        for key in self:
            value = self[key]
            yield key, value

class Metadata(MetadataWrapper):
    def __init__(self, filename):
        self.filename = filename
        if not os.path.exists(filename):
            self.types = {}
        else:
            json_obj = anyjson.deserialize(open(filename).read())
            self.types = json_obj['types']
            self.update(json_obj['data'])
