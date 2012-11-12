import os
import sys
import time

from datetime import datetime

from topic_modeling import anyjson
from topic_modeling.visualize.models import DatasetMetaInfo,\
    DatasetMetaInfoValue, Document, DocumentMetaInfo, DocumentMetaInfoValue,\
    AnalysisMetaInfo, AnalysisMetaInfoValue, TopicMetaInfo, TopicMetaInfoValue, WordType,\
    WordTypeMetaInfo, WordTypeMetaInfoValue, WordTokenMetaInfoValue, WordTokenMetaInfo

from topic_modeling.tools import TimeLongThing
import logging

logger = logging.getLogger('console')

datetime_format = "%Y-%m-%dT%H:%M:%S"

def import_dataset_metadata(dataset, dataset_metadata):
    logger.info('Importing dataset metadata...  ')
    sys.stdout.flush()
    start = datetime.now()

    for attribute, value in dataset_metadata[dataset.name].items():
        mi,__ = DatasetMetaInfo.objects.get_or_create(name=attribute)
        miv, ___ = DatasetMetaInfoValue.objects.get_or_create(info_type=mi, dataset=dataset)
        miv.set(value)
        miv.save()
    end = datetime.now()
    logger.info(' Done %s' % end - start)

def import_document_metadata(dataset, document_metadata):
    logger.info('Importing document metadata...  ')
    sys.stdout.flush()
    start = datetime.now()

    for filename, metadata in document_metadata.items():
        doc, _ = Document.objects.get_or_create(dataset=dataset, filename=filename)
        for attribute, value in metadata.items():
            mi,__ = DocumentMetaInfo.objects.get_or_create(name=attribute)
            miv, ___ = DocumentMetaInfoValue.objects.get_or_create(info_type=mi, document=doc)
            miv.set(value)
            miv.save()
    end = datetime.now()
    logger.info('  Done %s' % end - start)

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
    logger.info('  Done %s' % end - start)

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
    logger.info('  Done %s' % end - start)

def import_analysis_metadata(analysis, analysis_metadata):
    logger.info('Importing analysis metadata...  ',
    sys.stdout.flush()
    start = datetime.now()

    if analysis.name in analysis_metadata:
        for attribute, value in analysis_metadata[analysis.name].items():
            mi,__ = AnalysisMetaInfo.objects.get_or_create(name=attribute)
            miv, ___ = AnalysisMetaInfoValue.objects.get_or_create(info_type=mi, analysis=analysis)
            miv.set(value)
            miv.save()

    end = datetime.now()
    logger.info('  Done %s' % end - start)

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
    logger.info('  Done %s' % end - start)

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

