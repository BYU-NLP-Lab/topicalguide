from __future__ import division, print_function, unicode_literals

import os
import io
from itertools import chain
from dateutil import tz
from DateTime import DateTime
from django.db import models
from django.db import connection
from django.contrib import auth
from django.db.models import Avg, Count, Max, Sum

##############################################################################
# Database limitations.
##############################################################################

MAX_ELEMENTS_FOR_IN_OPERATOR = 500 # Database dependent.

##############################################################################
# Base/abstract tables used for inheritance.
##############################################################################

class Metric(models.Model):
    name = models.CharField(max_length=128, unique=True)
    
    def __unicode__(self):
        return unicode(self.name)

class MetricValue(models.Model):
    metric = models.ForeignKey('Metric')
    value = models.FloatField()
    
    class Meta(object):
        abstract = True
    
    def __unicode__(self):
        return unicode(self.value)

class MetadataType(models.Model):
    
    """\
    These are the supported types that the system knows how to handle.
    """
    INTEGER = 'int'
    FLOAT = 'float'
    TEXT = 'text'
    BOOLEAN = 'bool'
    DATETIME = 'datetime'
    ORDINAL = 'ordinal'
    DATATYPE_CHOICES = (
        (INTEGER, 'Integer'),
        (FLOAT, 'Float'),
        (TEXT, 'Text'),
        (BOOLEAN, 'Boolean'),
        (DATETIME, 'Date/Time'),
        (ORDINAL, 'Ordinal'),
    )
    
    """\
    Meanings are a way to label certain information so that certain metadatums
    can be used in a specific way.
    The meanings are used as follows:
    
    time -- allows the metric system to correctly select the right field for
            computing the temperature metric
    unknown -- the default
    """
    TIME = 'time'
    UNKNOWN = 'unknown'
    MEANING_CHOICES = (
        (TIME, 'Time'),
        (UNKNOWN, 'Unknown'),
    )
    
    dataset = models.ForeignKey('Dataset', related_name='metadata_types')
    name = models.CharField(max_length=128)
    datatype = models.CharField(max_length=32, choices=DATATYPE_CHOICES, default=TEXT)
    meaning = models.CharField(max_length=32, choices=MEANING_CHOICES, default=UNKNOWN, null=False)
    
    class Meta(object):
        unique_together = ('dataset', 'name', 'datatype')
    
    def __unicode__(self):
        is_ordinal = self.ordinal is not None
        return 'Name: %s\nDatatype: %s\nOrdinal: %s'%(unicode(self.name), unicode(self.datatype), unicode(is_ordinal))
    
    @staticmethod
    def get_allowed_types():
        return dict(MetadataType.DATATYPE_CHOICES)
    
    @staticmethod
    def determine_type(value):
        """\
        value -- a string
        Return the type of the value as a string.
        Return one of 'int', 'float', 'bool', 'text' (note that 'ordinal' must be
        user specified and cannot be determined simply by looking at it).
        Example: If value = '34' then the type returned MetadataType.INTEGER ('int').
        """
        try:
            int(value)
            return MetadataType.INTEGER
        except:
            pass
        try:
            float(value)
            return MetadataType.FLOAT
        except:
            pass
        lower_value = value.lower()
        if lower_value == 'true' or lower_value == 'false' or lower_value == 't' or lower_value == 'f':
            return MetadataType.BOOLEAN
        try:
            DateTime(value)
            return MetadataType.DATETIME
        except:
            pass
        return MetadataType.TEXT
    
    @staticmethod
    def is_supertype(super_type, sub_type):
        """\
        super_type -- a string representing the type
        sub_type -- a string representing the type
        Return true if super_type is considered a broader class; false otherwise.
        Heirarchy:
                      text
                       |
                  -----------------------------
                  /      \           \        \    
             float        datetime    bool     ordinal
               /
            int
        """
        if super_type == MetadataType.TEXT or super_type == sub_type:
            return True
        if super_type == MetadataType.FLOAT and sub_type == MetadataType.INTEGER:
            return True
        return False
        

class Ordinal(models.Model):
    """\
    Ordinals cannot have any holes in the values. It should start at zero \
    and any other values in the sequence must follow in order.
    Note that there can be multiple names for each value. This is done \
    because "Jan.", "Jan", "jan", "january", and "January" all map to the same \
    value in the sequence.
    """
    sequence = models.ForeignKey('MetadataType', related_name='ordinals') # An id for the entire sequence
    value = models.PositiveIntegerField()
    name = models.CharField(max_length=64)
    
    def __unicode__(self):
        return unicode(self.index) + ':' + value

class MetadataValue(models.Model):
    metadata_type = models.ForeignKey('MetadataType')
    bool_value = models.NullBooleanField(null=True)
    float_value = models.FloatField(null=True)
    int_value = models.IntegerField(null=True)
    text_value = models.TextField(null=True)
    datetime_value = models.DateTimeField(null=True)
    
    class Meta(object):
        abstract = True
    
    def __unicode__(self):
        return unicode(self.value())

    def set(self, value):
        value_type = self.metadata_type.datatype
        if value_type == MetadataType.FLOAT:
            self.float_value = float(value)
        elif value_type == MetadataType.TEXT or value_type == MetadataType.ORDINAL:
            self.text_value = unicode(value)
        elif value_type == MetadataType.INTEGER:
            self.int_value = int(value)
        elif value_type == MetadataType.BOOLEAN:
            self.bool_value = bool(value)
        elif value_type == MetadataType.DATETIME:
            self.datetime_value = DateTime(value).asdatetime()
        else:
            raise Exception("Values of type '{0}' aren't supported by MetadataValue".format(value_type))
    
    def value(self):
        result = None
        if self.float_value:
            result = self.float_value
        if self.text_value:
            if result: raise Exception("MetadataValues cannot be of more than one type.")
            result = self.text_value
        if self.int_value:
            if result: raise Exception("MetadataValues cannot be of more than one type.")
            result = self.int_value
        if self.bool_value:
            if result: raise Exception("MetadataValues cannot be of more than one type.")
            result = self.bool_value
        if self.datetime_value:
            if result: raise Exception("MetadataValues cannot be of more than one type.")
            result = unicode(self.datetime_value)
        return result

    def type(self):
        return self.metadata_type.datatype

##############################################################################
# Tables for gathering statistics.
##############################################################################

class CountType(models.Model):
    name=models.CharField(max_length=128)

class CountValue(models.Model):
    type = models.ForeignKey('CountType')
    timestamp = models.DateTimeField()
    
    class Meta(object):
        unique_together = ('type', 'timestamp')

class IPAddresses(models.Model):
    type = models.ForeignKey('CountType')
    ip_address = models.CharField(max_length=128)
    
    class Meta(object):
        unique_together = ('type', 'ip_address')

##############################################################################
# Tables for tracking views.
##############################################################################

class View(models.Model):
    url_hash = models.CharField(max_length=128) # TODO get actual length and type of hash (text hash or long integer???)
    url = models.URLField(max_length=10000)
    favorite_users = \
        models.ManyToManyField('auth.User', related_name='favorite_views')
    
    class Meta(object):
        unique_together = ('url_hash', 'url')

##############################################################################
# Table to track external datasets.
##############################################################################

class ExternalDataset(models.Model):
    """Tracks external datasets by storing a json string representing the database settings."""
    name = models.SlugField(unique=True)
    database_settings = models.TextField()
    # Used by the database router to correctly route the table creation and usage correctly
    _MODEL_NAME = 'ExternalDataset'

##############################################################################
# Tables for datasets, documents, and their respective metadata and metrics.
##############################################################################

class Dataset(models.Model):
    name = models.SlugField(unique=True)
    dataset_dir = models.CharField(max_length=128)
    # Indicates if the dataset can be viewed by the public, private otherwise.
    public = models.BooleanField(default=False)
    # Indicates if the dataset is visible to anyone.
    visible = models.BooleanField(default=False)
    last_updated = models.DateTimeField(auto_now=True)
    # Indicates if the raw text of documents is available.
    public_documents = models.BooleanField(default=False)
    
    favorite_users = \
        models.ManyToManyField('auth.User', related_name='favorite_datasets')
    authorized_users = \
        models.ManyToManyField('auth.User', related_name='private_datasets')
    
    def __unicode__(self):
        return self.name
    
    def get_document_metadata_types(self):
        query = self.documents.values_list('metadata_values__metadata_type__name', 'metadata_values__metadata_type__datatype').distinct()
        query2 = self.empty_document_metadata_types.values_list('metadata_type__name', 'metadata_type__datatype').distinct()
        result = {}
        for name, datatype in chain(query, query2):
            result[name] = datatype
        return result
    
    def get_document_metadata_meanings(self):
        query = self.documents.values_list('metadata_values__metadata_type__name', 'metadata_values__metadata_type__meaning').distinct()
        query2 = self.empty_document_metadata_types.values_list('metadata_type__name', 'metadata_type__meaning').distinct()
        result = {}
        for name, meaning in chain(query, query2):
            result[name] = meaning
        return result
    
    def get_document_metadata_ordinals(self):
        query = self.documents.values_list('metadata_values__metadata_type__name', 
                                           'metadata_values__metadata_type__datatype', 
                                           'metadata_values__metadata_type__ordinals__value',
                                           'metadata_values__metadata_type__ordinals__name')\
                                           .distinct()\
                                           .order_by('metadata_values__metadata_type__ordinals__value')
        result = {}
        for meta_name, datatype, index, ord_name in query:
            if datatype == MetadataType.ORDINAL:
                array = result.setdefault(meta_name, [])
                if index >= len(array):
                    array.append([ord_name])
                else:
                    array[index].append(ord_name)
        return result
    
    @property
    def readable_name(self):
        """Return a human readable name."""
        try:
            return self.metadata_values.get(metadata_type__name='readable_name').value()
        except:
            return self.name.replace('_', ' ').title()
    
    @property
    def description(self):
        """Return a description of the dataset."""
        try:
            return self.metadata_values.get(metadata_type__name='description').value()
        except:
            return 'No description available.'
    
    def delete(self, *args, **kwargs):
        """Remove everything pertaining to this dataset."""
        if self.analyses.exists():
            self.analyses.delete()
        if self.documents.exists():
            self.documents.delete()
        if self.metadata_values.exists():
            self.metadata_values.delete()
        if datasetmetricvalues.exists():
            datasetmetricvalues.delete()
        super(Dataset, self).delete(*args, **kwargs)

class DatasetMetadataValue(MetadataValue):
    dataset = models.ForeignKey('Dataset', related_name='metadata_values')

class DatasetEmptyDocumentMetadataType(models.Model):
    dataset = models.ForeignKey('Dataset', related_name='empty_document_metadata_types')
    metadata_type = models.ForeignKey('MetadataType')

class DatasetMetricValue(MetricValue):
    dataset = models.ForeignKey('Dataset', related_name='metric_values')

class Document(models.Model):
    dataset = models.ForeignKey('Dataset', related_name='documents')
    index = models.PositiveIntegerField()
    filename = models.CharField(max_length=128)
    source = models.URLField(max_length=1000)
    length = models.PositiveIntegerField()
    
    favorite_users = \
        models.ManyToManyField('auth.User', related_name='favorite_documents')
    
    class Meta(object):
        unique_together = ('dataset', 'filename')
        unique_together = ('dataset', 'index')
    
    def __unicode__(self):
        return unicode(self.filename)
    
    def get_metadata(self):
        result = {}
        for m in self.metadata_values.all():
            result[m.metadata_type.name] = m.value()
        return result
    
    def get_content(self):
        filepath = os.path.join(self.dataset.dataset_dir, 'documents', self.filename)
        try:
            with io.open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except:
            content = 'Error occurred while trying to access content.'
        return content
	
    def get_intro_snippet(self):
		snippet = self.get_content()[0: 200]
		index = snippet.rfind(' ')
		return snippet[0:index]+' ...'
    
    def get_key_word_in_context(self, token_indices, pre=80, post=80):
        word_tokens = self.tokens.filter(token_index__in=token_indices).order_by("start_index")
        
        result = {}
        text = self.get_content()
        for token in word_tokens:
            pre_word = pre
            start = token.start_index - pre_word
            if start < 0:
                pre_word = token.start_index
                start = 0
            word_len = len(token.word_type.word)
            post_word = post
            before = text[start: token.start_index]
            word = text[token.start_index: token.start_index+word_len]
            after = text[token.start_index+word_len: token.start_index+word_len+post_word]
            result[token.token_index] = [before, word, after, token.word_type.word]
        return result
    
    def get_word_token_topics_and_locations(self, analysis, words=[]):
        """
        Gather word token information including start index and the topic.
        Note that the end index can be inferred by the word length and is thus omitted.
        Return a dictionary of the form result[word] = [(topic, start_index), ...].
        """
        if words == '*':
            tokens = self.tokens.filter(topics__analysis=analysis)
        else:
            tokens = self.tokens.filter(topics__analysis=analysis, word_type__word__in=words)
        tokens = tokens.select_related()
        result = {}
        for token in tokens:
            t = token.word_type.word
            if t not in result:
                result[t] = []
            result[t].append((token.topics.filter(analysis=analysis)[0].number, token.start_index))
        return result
    
    def get_top_n_words(self, words='*', top_n=10):
        word_counts = self.tokens.values_list('word_type__word').annotate(count=Count('word_type__word'))
        if words != '*':
            word_counts = word_counts.filter(word_type__word__in=words)
        word_counts = word_counts.order_by('-count')
        return {row[0]: {'token_count': row[1]} for row in word_counts[:top_n]}

class DocumentMetadataValue(MetadataValue):
    document = models.ForeignKey('Document', related_name='metadata_values')
    
    def __unicode__(self):
        return '[%s(%s)=%s]'%(self.metadata_type.name, self.document.filename, self.value())

class DocumentMetricValue(MetricValue):
    document = models.ForeignKey('Document', related_name='metric_values')

class DocumentAnalysisMetricValue(MetricValue):
    document = models.ForeignKey('Document', related_name='document_analysis_metric_values')
    analysis = models.ForeignKey('Analysis', related_name='document_analysis_metric_values')

class DocumentPairwiseMetricValue(MetricValue):
    origin_document = models.ForeignKey('Document', related_name='origininating_metric_values')
    ending_document = models.ForeignKey('Document', related_name='ending_metric_values')
    analysis = models.ForeignKey('Analysis', related_name='document_pairwise_metric_values')

##############################################################################
# Tables for analysis, topics, topic names, and metadata.
##############################################################################

class Analysis(models.Model):
    name = models.SlugField(max_length=128)
    dataset = models.ForeignKey('Dataset', related_name='analyses')
    last_updated = models.DateTimeField(auto_now=True)
    
    word_types = models.ManyToManyField('WordType', through='WordToken', through_fields=('analysis', 'word_type'), related_name='word_type_analyses')
    stopwords = models.ManyToManyField('WordType', through='Stopword', related_name='stopword_analyses')
    excluded_words = models.ManyToManyField('WordType', through='ExcludedWord', related_name='excluded_word_analyses')
    favorite_users = \
        models.ManyToManyField('auth.User', related_name='favorite_analyses')
    
    def __unicode__(self):
        return self.name
    
    def get_stopwords(self):
        stopwords = set()
        for s in self.stopwords.all():
            stopwords.add(s)
        return stopwords
    
    @property
    def readable_name(self):
        """Return a human readable name."""
        try:
            return self.metadata_values.get(metadata_type__name='readable_name').value()
        except:
            return self.name.replace('_', ' ').title()
    
    @property
    def description(self):
        """Return a description of the dataset."""
        try:
            return self.metadata_values.get(metadata_type__name='description').value()
        except:
            return 'No description available.'
    
    def topic_word_type_occurrences(self):
        """Find the number of times a word type (not token) is assigned to a topic.
        Return a dict with word types as the keys and topic counts as the values.
        """
        word_type_query = self.topics.values_list('number', 'tokens__word_type__word').distinct()
        result = {}
        for _, word in word_type_query:
            result[word] = result.setdefault(word, 0) + 1
        return result
    
    def get_topic_name_schemes(self):
        """Return a list of all topic name schemes available for this analysis."""
        result = []
        query = self.topics.values_list("schemes__name").distinct()
        for row in query:
            result.append(row[0])
        return result

class AnalysisMetadataValue(MetadataValue):
    analysis = models.ForeignKey('Analysis', related_name='metadata_values')

class AnalysisMetricValue(MetricValue):
    analysis = models.ForeignKey('Analysis', related_name='metric_values')

class Topic(models.Model):
    analysis = models.ForeignKey('Analysis', related_name='topics')
    number = models.PositiveIntegerField()
    parent = models.ForeignKey('self', related_name='children', null=True, default=None)
    
    schemes = models.ManyToManyField('TopicNameScheme', through='TopicName')
    favorite_users = \
        models.ManyToManyField('auth.User', related_name='favorite_topics')
    tokens = models.ManyToManyField('WordToken', through='WordTokenTopic', related_name='topics')
    
    class Meta(object):
        unique_together = ('analysis', 'number')
    
    def word_token_type_counts(self, words='*'):
        """Return a dict of all word types mapped to token word type counts."""
        topic_words = self.tokens.values('word_type__word').annotate(count=Count('word_type__word'))
        if words != '*':
            topic_words = topic_words.filter(word_type__word__in=words)
        topic_words = topic_words.order_by('-count')
        return {value['word_type__word']: value['count'] for value in topic_words}
    
    def top_n_words(self, words='*', top_n=10, metadata_name=None, metadata_type=None, metadata_value=None, metadata_range=None):
        topic_words = self.tokens.values('word_type__word').annotate(count=Count('word_type__word'))
        # Word filter
        if words != '*':
            topic_words = topic_words.filter(word_type__word__in=words)
        # Metadata filter
        if metadata_name and metadata_type:
            topic_words = topic_words.filter(document__metadata_values__metadata_type__name=metadata_name, \
                document__metadata_values__metadata_type__datatype=metadata_type)
            if metadata_value:
                if metadata_type == MetadataType.TEXT or metadata_type == MetadataType.ORDINAL:
                    topic_words = topic_words.filter(document__metadata_values__text_value=metadata_value)
                elif metadata_type == MetadataType.INTEGER:
                    topic_words = topic_words.filter(document__metadata_values__int_value=int(metadata_value))
                elif metadata_type == MetadataType.FLOAT:
                    topic_words = topic_words.filter(document__metadata_values__float_value=float(metadata_value))
                elif metadata_type == MetadataType.BOOLEAN:
                    topic_words = topic_words.filter(document__metadata_values__bool_value=bool(metadata_value))
            if metadata_range:
                if metadata_type == MetadataType.INTEGER:
                    topic_words = topic_words.filter(document__metadata_values__int_value__range=(metadata_range[0], metadata_range[1]))
                elif metadata_type == MetadataType.FLOAT:
                    topic_words = topic_words.filter(document__metadata_values__float_value__range=(metadata_range[0], metadata_range[1]))
                elif metadata_type == MetadataType.ORDINAL:
                    ordinals = Ordinal.objects.values_list('name').filter(sequence__name=metadata_name, sequence__datatype=metadata_type, value__range=(metadata_range[0], metadata_range[1]))
                    ord_list = [row[0] for row in ordinals]
                    topic_words = topic_words.filter(document__metadata_values__text_value__in=ord_list)
        topic_words = topic_words.order_by('-count')
        return {value['word_type__word']: {'token_count': value['count']} for value in topic_words[:top_n]}
    
    def top_n_documents(self, documents='*', top_n=10):
        topicdocs = self.tokens.values('document__id', 'document__filename').annotate(count=Count('document__id'))
        if documents != '*':
            topicdocs = topicdocs.filter(document__filename__in=documents)
        topicdocs = topicdocs.order_by('-count')
        return {value['document__filename']: {'token_count': value['count']} for value in topicdocs[:top_n]}
    
    def get_word_tokens(self, words='*'):
        if words == '*':
            word_tokens = self.tokens.all()
        else:
            word_tokens = self.tokens.filter(word_type__word__in=words)
        
        result = {}
        for token in word_tokens:
            word_type = token.word_type.word
            if word_type not in result:
                result[word_type] = []
            result[word_type].append([token.document.filename, token.token_index])
        return result
    
    def get_word_token_documents_and_locations(self, documents=[]):
        """
        Get all word token start and end indices according to documents.
        Return a dictionary of the form result[document] = [(start, end), ...].
        """
        if documents == '*':
            tokens = self.tokens.all()
        else:
            tokens = self.tokens.filter(document__filename__in=documents)
        result = {}
        for token in tokens:
            doc = token.document.filename
            if doc not in result:
                result[doc] = []
            start = token.start_index
            result[doc].append((start, start+len(token.word_type.word)))
        return result
    
    def get_pairwise_metrics(self, options):
        pairwise = self.originating_metric_values.all()
        if 'topic_pairwise' in options and options['topic_pairwise'] != '*':
            pairwise = pairwise.filter(metric__in=options['topic_pairwise'])
        result = {}
        topicCount = Topic.objects.filter(analysis=self.analysis).count()
        for value in pairwise:
            if not value.metric.name in result:
                result[value.metric.name] = [0 for i in range(topicCount)]
            result[value.metric.name][value.ending_topic.number] = value.value
        return result

class TopicMetadataValue(MetadataValue):
    topic = models.ForeignKey('Topic', related_name='metadata_values')

class TopicMetricValue(MetricValue):
    topic = models.ForeignKey('Topic', related_name='metric_values')

class TopicPairwiseMetricValue(MetricValue):
    origin_topic = models.ForeignKey('Topic', related_name='originating_metric_values')
    ending_topic = models.ForeignKey('Topic', related_name='ending_metric_values')

class TopicWordTypeMetric(MetricValue):
    topic = models.ForeignKey('Topic', related_name='word_type_metric_values')
    word_type = models.ForeignKey('WordType', related_name='topic_metric_values')

class TopicNameScheme(models.Model):
    name = models.CharField(max_length=128, unique=True)
    
    def __unicode__(self):
        return unicode(self.name)

class TopicName(models.Model):
    topic = models.ForeignKey('Topic', related_name='names')
    name_scheme = models.ForeignKey('TopicNameScheme', related_name='names')
    name = models.CharField(max_length=128)
    
    class Meta(object):
        unique_together = ('topic', 'name_scheme')
    
    def __unicode__(self):
        return unicode(self.name)

##############################################################################
# Tables for tokenization schemes, tokens, word types, word representations.
##############################################################################

class WordType(models.Model):
    """This stores how a word is spelled."""
    word = models.CharField(max_length=128, unique=True)
    
    def __unicode__(self):
        return unicode(self.word)

# Warning: this class doesn't have an auto-incrementing primary key.
class WordToken(models.Model):
    """Tracks the sequence of instances of word types in a document."""
    id = models.IntegerField(primary_key=True)
    analysis = models.ForeignKey('Analysis', related_name='tokens')
    document = models.ForeignKey('Document', related_name='tokens')
    word_type = models.ForeignKey('WordType', related_name='tokens')
    word_type_abstraction = models.ForeignKey('WordType', related_name='word_type_abstraction_tokens')
    # Where the token is in the token sequence.
    token_index = models.PositiveIntegerField()
    # Where the token begins in the original document text, a character offset.
    start_index = models.PositiveIntegerField()
    
    class Meta(object):
        unique_together = ('analysis', 'document', 'token_index')
    
    def __unicode__(self):
        return self.word_type

class WordTokenTopic(models.Model):
    """Attaches topics to tokens."""
    token = models.ForeignKey('WordToken')
    topic = models.ForeignKey('Topic')
    
    class Meta(object):
        unique_together = ('token', 'topic')

class Stopword(models.Model):
    """Explicit many-to-many relationship to map analyses to words."""
    analysis = models.ForeignKey('Analysis')
    word_type = models.ForeignKey('WordType')
    
    class Meta(object):
        unique_together = ('analysis', 'word_type')

class ExcludedWord(models.Model):
    """Explicit many-to-many relationship to map analyses to words."""
    analysis = models.ForeignKey('Analysis')
    word_type = models.ForeignKey('WordType')
    
    class Meta(object):
        unique_together = ('analysis', 'word_type')

