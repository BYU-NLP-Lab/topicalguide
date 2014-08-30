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

import os
import random
import time
from datetime import datetime

from django.db import models
from django.db.models.aggregates import Count

from topic_modeling.anyjson import deserialize



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
# Tables for datasets, documents, and words.
##############################################################################

class Dataset(models.Model):
    name = models.SlugField(unique=True)
    dataset_dir = models.CharField(max_length=128, db_index=True)
    files_dir = models.CharField(max_length=128, db_index=True)
    visible = models.BooleanField(default=True)
    
    FIELDS = {
        'metadata': lambda x: {miv.info_type.name: miv.value() for miv in x.metainfovalues.iterator()},
        'metrics': lambda x: {mv.metric.name: mv.value for mv in x.datasetmetricvalues.iterator()},
        'document_count': lambda dataset: dataset.documents.count(),
        'analysis_count': lambda dataset: dataset.analyses.count(),
    }
    
    def __unicode__(self):
        return self.name

    def all_words(self):
        # select * from visualize_
        return WordType.objects.filter(tokens__document__dataset=self)

    def delete(self, *args, **kwargs):
        """Remove everything pertaining to this dataset."""
        if self.analyses.exists():
            self.analyses.delete()
        if self.documents.exists():
            self.documents.delete()
        if self.metainfovalues.exists():
            self.metainfovalues.delete()
        if datasetmetricvalues.exists():
            datasetmetricvalues.delete()
        super(Dataset, self).delete(*args, **kwargs)
    
    @property
    def identifier(self):
        return self.name
    
    # Take a set of field names ['metadata', 'metrics'] and return the appropriate values
    def fields_to_dict(self, fields):
        result = {}
        for f in fields:
            if f in self.FIELDS:
                result[f] = self.FIELDS[f](self)
        return result
    
    @property
    def readable_name(self):
        """Return a human readable name."""
        try:
            return self.metainfovalues.get(info_type__name='readable_name').value()
        except:
            return self.name.replace('_', ' ').title()
    
    @property
    def description(self):
        """Return a description of the dataset."""
        try:
            return self.metainfovalues.get(info_type__name='description').value()
        except:
            return 'No description available.'


LEFT_CONTEXT_SIZE = 40
RIGHT_CONTEXT_SIZE = 40
class Document(models.Model):
    # Warning: this class doesn't have an auto-incrementing primary key.
    id = models.IntegerField(primary_key=True)
    filename = models.CharField(max_length=128, db_index=True)
    full_path = models.TextField()
    dataset = models.ForeignKey(Dataset, related_name='documents')
    
    ATTRIBUTES = {
        'metadata': lambda doc: {miv.info_type.name: miv.value() for miv in doc.metainfovalues.iterator()},
        'metrics': lambda doc: {mv.metric.name: mv.value for mv in doc.documentmetricvalues.iterator()},
        'text': lambda doc: doc.get_text(),
    }
    
    @property
    def identifier(self):
        return self.filename
    
    def __unicode__(self):
        return unicode(self.filename)

    def attributes_to_dict(self, attributes, options):
        result = {}
        for attr in attributes:
            if attr in self.ATTRIBUTES:
                result[attr] = self.ATTRIBUTES[attr](self)
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
            tokens = self.tokens.filter(topics__analysis=analysis, type__type__in=words)
        tokens.select_related()
        result = {}
        for token in tokens:
            t = token.type.type
            if t not in result:
                result[t] = []
            result[t].append((token.topics.filter(analysis=analysis)[0].number, token.start))
        return result
    
    def get_context_for_word(self, word_to_find, analysis, topic=None):
        '''Get the word in context

        Args:
            word_to_find: str
            analysis:     Analysis
            topic:      Topic or None

        Return:
            (leftofword:str, word:str, rightofword:str)

        '''
        word_type = WordType.objects.get(type=word_to_find)
        if topic is None:
            tokens = self.tokens.filter(type=word_type)
        else:
            topic = analysis.topics.get(number=int(topic))
            tokens = topic.tokens.filter(type=word_type, document=self)
        tokens = list(tokens)
        token = random.choice(tokens)
        context = self.tokens.all()[max(0, token.token_index - LEFT_CONTEXT_SIZE):token.token_index + RIGHT_CONTEXT_SIZE]
        left_context = ' '.join([tok.type.type for tok in context[:LEFT_CONTEXT_SIZE]])
        right_context = ' '.join([tok.type.type for tok in context[LEFT_CONTEXT_SIZE + 1:]])

        return left_context, token.type.type, right_context

    before_text = '<span style="color: blue;">'
    after_text = '</span>'

    def get_highlighted_text(self, topics, analysis):
        parts = list()
        highlight_me = self.tokens.filter(topics__in=topics).all()

        for token in self.tokens.all():
            highlight = token in highlight_me
            if highlight:
                parts.append(self.before_text)
            parts.append(token.type.type)
            if highlight:
                parts.append(self.after_text)
        return ' '.join(parts)
    
    def html(self, kwic=None):
        return self.text(kwic)
    
    def get_text(self):
        """Return the unicode text of the file used as input to the analyses."""
        with open(self.full_path, 'r') as fin:
            return unicode(fin.read().decode('utf-8'))
    
    def get_key_word_in_context(self, token_indices, pre=80, post=80):
        word_tokens = self.tokens.filter(token_index__in=token_indices).order_by("start")
        
        result = {}
        text = self.get_text()
        for token in word_tokens:
            pre_word = pre
            start = token.start - pre_word
            if start < 0:
                pre_word = token.start
                start = 0
            word_len = len(token.type.type)
            post_word = post
            before = text[start: token.start]
            word = text[token.start: token.start+word_len]
            after = text[token.start+word_len: token.start+word_len+post_word]
            result[token.token_index] = [before, word, after, token.type.type]
        return result
    
    def get_top_topics(self, analysis, document):
        w = Widget('Top Topics', 'documents/top_topics')
        from django.db import connection
        c = connection.cursor()
        c.execute('''SELECT wtt.topic_id, count(*) as cnt
                        FROM visualize_wordtoken wt
                        JOIN visualize_wordtoken_topics wtt
                         on wtt.wordtoken_id = wt.id
                        JOIN visualize_topic t
                         on t.id = wtt.topic_id
                            WHERE t.analysis_id = %d AND wt.document_id = %d
                            GROUP BY wtt.topic_id
                            ORDER BY cnt DESC'''%(analysis.id,document.id))
        rows = c.fetchall()[:10]
        total = 0
        for obj in rows:
            total += obj[1]
        topics = []
        for obj in rows:
            topic_name = TopicName.objects.filter(topic__id=obj[0])[0]
            t = WordSummary(topic_name, float(obj[1]) / total)
            topics.append(t)
        w['chart_address'] = get_chart(topics)
        return w
    
    def text(self, kwic=None):
        #file_dir = self.dataset.files_dir
        text = open(self.full_path, 'r').read().decode('utf-8')
        if kwic:
            beg_context, end_context = self.get_kwic_context_ends(kwic, text)
            if beg_context >= 0:
                text = text[:beg_context] + \
                        '<span style=\"text-decoration: underline;\">' + \
                        text[beg_context:end_context] + '</span>' + \
                        text[end_context:]

        text = unicode(text)
        for item in (' ;', ' .', ' ,', ' )', '( ', ' !', ' :'):
            text = text.replace(item, item.strip())

        text = text.splitlines()
        text = [line for line in text if line]
        return '<br><br>'.join(text)
    
    def get_text_for_kwic(self):
        return open(self.dataset.dataset_dir + "/" +
            self.filename, 'r').read()

    def get_kwic_context_word(self, word, text=None):
        if text is None:
            text = self.get_text_for_kwic()

        beg_word = text.lower().rfind(" " + word + " ")
        if beg_word >= 0:
            end_word = beg_word + len(word) + 1
            return beg_word, end_word
        else:
            return - 1, -1

    def get_kwic_context_ends(self, word, text=None):
        context_size = 50

        if text is None:
            text = self.get_text_for_kwic()

        beg_word, end_word = self.get_kwic_context_word(word, text)

        if beg_word >= 0:
            beg_context = text.find(' ', beg_word - context_size) + 1
            beg_context = max(0, beg_context)
            end_context = text.rfind(' ', end_word, end_word + context_size)
            end_context = min(len(text), end_context)
            return beg_context, end_context
        else:
            return - 1, -1

    def get_title(self):
        try:
            return self.metainfovalues.get(info_type__name='title').value
        except DocumentMetaInfoValue.DoesNotExist:
            return self.filename

    def word_count(self):
        return self.tokens.count()

    class Meta:
        ordering = ['dataset', 'filename']


class WordType(models.Model):
    # Warning: this class doesn't have an auto-incrementing primary key.
    id = models.IntegerField(primary_key=True)
    type = models.CharField(max_length=128, db_index=True) #@ReservedAssignment
    
    def __unicode__(self):
        return unicode(self.type)

    def __str__(self):
        return self.type

class WordToken(models.Model):
    # Warning: this class doesn't have an auto-incrementing primary key.
    id = models.IntegerField(primary_key=True)
    type = models.ForeignKey(WordType, related_name='tokens')
    token_index = models.IntegerField()
    start = models.IntegerField()
    
    document = models.ForeignKey(Document, related_name='tokens')
    topics = models.ManyToManyField('Topic', related_name='tokens')

    def __unicode__(self):
        return '[%s,%s]' % (self.type.type, self.token_index)
    
    def get_max_pk(self, database_id='default'):
        """Return the largest primary key/id for these objects."""
        return WordToken.objects.using(database_id).all().aggregate(Max('id'))['id__max']


##############################################################################
# Tables for analyses, and topics.
##############################################################################

class Analysis(models.Model):
    dataset = models.ForeignKey(Dataset, related_name='analyses')
    stopwords = models.ManyToManyField(WordToken)
    name = models.SlugField()
    working_dir_path = models.CharField(max_length=128)
    
    FIELDS = {
        'metadata': lambda analysis: {miv.info_type.name: miv.value() for miv in analysis.metainfovalues.iterator()},
        'metrics': lambda analysis: {mv.metric.name: mv.value for mv in analysis.analysismetricvalues.iterator()},
    }
    
    def __unicode__(self):
        return self.name

    def delete(self, *args, **kwargs):
        for topic in self.topics.all():
            print "\tremove topic " + str(topic)
            topic.delete()

        super(Analysis, self).delete(*args, **kwargs)
    
    @property
    def identifier(self):
        return self.name
    
    def fields_to_dict(self, fields):
        result = {}
        for f in fields:
            if f in self.FIELDS:
                result[f] = self.FIELDS[f](self)
        return result
    
    @property
    def readable_name(self):
        """Return a human readable name."""
        try:
            return self.metainfovalues.get(info_type__name='readable_name').value
        except:
            return self.name.replace('_', ' ').title()
    
    @property
    def description(self):
        """Return a description of the analysis."""
        try:
            return self.metainfovalues.get(info_type__name='description').value
        except:
            return 'No description available.'
    
    class Meta:
        unique_together = ('dataset', 'name')

class Topic(models.Model):
    number = models.IntegerField()
    analysis = models.ForeignKey(Analysis, related_name='topics')
    metrics = models.ManyToManyField('TopicMetric', through='TopicMetricValue')
    
    ATTRIBUTES = {
        'metadata': lambda topic: {miv.info_type.name: miv.value() for miv in topic.metainfovalues.iterator()},
        'metrics': lambda topic: {mv.metric.name: mv.value for mv in topic.topicmetricvalues.iterator()},
        'names': lambda topic: {name.name_scheme.name: name.name for name in topic.names.iterator()},
    }
    
    @property
    def identifier(self):
        return self.number
    
    def attributes_to_dict(self, attributes, options):
        result = {}
        for attr in attributes:
            if attr in self.ATTRIBUTES:
                result[attr] = self.ATTRIBUTES[attr](self)
            if attr == 'pairwise':
                result[attr] = self.get_pairwise_metrics(options)
        return result
    
    def __unicode__(self):
        names = TopicName.objects.filter(topic=self)
        if names.count():
            name = names[0].name
        else:
            name = ' -- '
        return '%d: %s' % (self.number, name)
    
    def get_word_tokens(self, words='*'):
        if words == '*':
            word_tokens = self.tokens.all()
        else:
            word_tokens = self.tokens.filter(type__type__in=words)
        
        result = {}
        for token in word_tokens:
            word_type = token.type.type
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
            doc = token.document.identifier
            if doc not in result:
                result[doc] = []
            start = token.start
            result[doc].append((start, start+len(token.type.type)))
        return result
    
    def get_pairwise_metrics(self, options):
        pairwise = self.pairwisetopicmetricvalue_originating.all()
        if 'topic_pairwise' in options and options['topic_pairwise'] != '*':
            pairwise = pairwise.filter(metric__in=options['topic_pairwise'])
        pairwise.select_related()
        result = {}
        topicCount = Topic.objects.filter(analysis=self.analysis).count()
        for value in pairwise:
            if not value.metric.name in result:
                result[value.metric.name] = [0 for i in range(topicCount)]
            result[value.metric.name][value.topic2.number] = value.value
        return result
    
    def total_count(self):
        return self.tokens.count()
    
    def top_n_words(self, words='*', top_n=10):
        topic_words = self.tokens.values('type__type').annotate(count=Count('type__type'))
        if words != '*':
            topic_words = topic_words.filter(type__type__in=words)
        topic_words = topic_words.order_by('-count')
        return {value['type__type']: {'token_count': value['count']} for value in topic_words[:top_n]}
    
    def top_n_documents(self, documents='*', top_n=10):
        topicdocs = self.tokens.values('document__id', 'document__filename').annotate(count=Count('document__id'))
        if documents != '*':
            topicdocs = topicdocs.filter(document__filename__in=documents)
        topicdocs = topicdocs.order_by('-count')
        return {value['document__filename']: {'token_count': value['count']} for value in topicdocs[:top_n]}
    
    def top_n_topics(self, top_n=10):
        raise Exception('top_n_topics not implemented yet.')
        
    
    def topic_word_counts(self, sort=False):
        topicwords = self.tokens.values('type__type').annotate(count=Count('type__type'))
        if sort:
            topicwords = topicwords.order_by('-count')
        return topicwords
        
    def topic_document_counts(self, sort=False):
        topicdocs = self.tokens.values('document__id', 'document__filename').annotate(count=Count('document__id'))
        if sort:
            topicdocs = topicdocs.order_by('-count')
        return topicdocs

# This class is to explicitly access a many-to-many table to optimize adding to a database
class WordToken_Topics(models.Model):
    # Warning: this class doesn't have an auto-incrrementing primary key.
    id = models.IntegerField(primary_key=True)
    wordtoken = models.ForeignKey(WordToken, related_name='topic_relations')
    topic = models.ForeignKey(Topic, related_name='word_relations')

class TopicGroup(Topic):
    @property
    def subtopics(self):
        return [topicgrouptopic.topic for topicgrouptopic \
                in TopicGroupTopic.objects.filter(group=self)]

class TopicGroupTopic(models.Model):
    topic = models.ForeignKey(Topic)
    group = models.ForeignKey(TopicGroup, related_name='group')

class TopicNameScheme(models.Model):
    analysis = models.ForeignKey(Analysis, related_name='topicnameschemes')
    name = models.CharField(max_length=128)

    def __unicode__(self):
        return self.name

class TopicName(models.Model):
    topic = models.ForeignKey(Topic, related_name='names')
    name_scheme = models.ForeignKey(TopicNameScheme, related_name='names')
    name = models.CharField(max_length=128)

    def __str__(self):
        return self.name

##############################################################################
# Tables for metrics.
##############################################################################

class Metric(models.Model):
    name = models.CharField(max_length=128)
    class Meta:
        abstract = True

    def __str__(self):
        return self.name

class PairwiseMetric(Metric):
    pass
    class Meta:
        abstract = True

class MetricValue(models.Model):
    value = models.FloatField()
    class Meta:
        abstract = True

    def __str__(self):
        return str(self.value)

class DatasetMetric(Metric):
    pass

class DatasetMetricValue(MetricValue):
    dataset = models.ForeignKey(Dataset, related_name='datasetmetricvalues')
    metric = models.ForeignKey(DatasetMetric, related_name='values')

class AnalysisMetric(Metric):
    pass

class AnalysisMetricValue(MetricValue):
    analysis = models.ForeignKey(Analysis, related_name='analysismetricvalues')
    metric = models.ForeignKey(AnalysisMetric, related_name='values')

class TopicMetric(Metric):
    analysis = models.ForeignKey(Analysis, related_name='topicmetrics')

    def __unicode__(self):
        return self.name

class TopicMetricValue(MetricValue):
    topic = models.ForeignKey(Topic, related_name='topicmetricvalues')
    metric = models.ForeignKey(TopicMetric, related_name='values')

class PairwiseTopicMetric(PairwiseMetric):
    analysis = models.ForeignKey(Analysis, related_name='pairwisetopicmetrics')

    def __unicode__(self):
        return self.name + ': ' + self.analysis.name

class PairwiseTopicMetricValue(MetricValue):
    topic1 = models.ForeignKey(Topic,
            related_name='pairwisetopicmetricvalue_originating')
    topic2 = models.ForeignKey(Topic,
            related_name='pairwisetopicmetricvalue_ending')
    metric = models.ForeignKey(PairwiseTopicMetric, related_name='values')

    def __unicode__(self):
        return '%s(%s, %s) = %d' % (self.metric.name, self.topic1.names,
                self.topic2.names, self.value)

class DocumentMetric(Metric):
    analysis = models.ForeignKey(Analysis, related_name='documentmetrics')

    def __unicode__(self):
        return self.name

class DocumentMetricValue(MetricValue):
    document = models.ForeignKey(Document, related_name='documentmetricvalues')
    metric = models.ForeignKey(DocumentMetric, related_name='values')

class PairwiseDocumentMetric(PairwiseMetric):
    analysis = models.ForeignKey(Analysis, related_name='pairwisedocumentmetrics')

    def __unicode__(self):
        return self.name + ': ' + self.analysis.name

class PairwiseDocumentMetricValue(MetricValue):
    document1 = models.ForeignKey(Document,
            related_name='pairwisedocumentmetricvalue_originating')
    document2 = models.ForeignKey(Document,
            related_name='pairwisedocumentmetricvalue_ending')
    metric = models.ForeignKey(PairwiseDocumentMetric, related_name='values')

    def __unicode__(self):
        return '%s(%s, %s) = %d' % (self.metric.name, self.document1.filename,
                self.document2.filename, self.value)

class WordTypeMetric(Metric):
    pass

class WordTypeMetricValue(MetricValue):
    type = models.ForeignKey(WordType, related_name='wordtypemetricvalues')
    metric = models.ForeignKey(WordTypeMetric, related_name='values')

class WordTokenMetric(Metric):
    pass

class WordTokenMetricValue(MetricValue):
    token = models.ForeignKey(WordToken, related_name='wordtokenmetricvalues')
    metric = models.ForeignKey(WordTokenMetric, related_name='values')

##############################################################################
# Tables for metadata.
##############################################################################

#TODO Store the data type as a field in the MetaInfo class
class MetaInfo(models.Model):
    name = models.CharField(max_length=128, db_index=True)

    def __str__(self):
        return self.name

    class Meta:
        abstract = True

class MetaInfoValue(models.Model):
    # Warning: this class doesn't have an auto-incrrementing primary key.
    id = models.IntegerField(primary_key=True)
    bool_value = models.NullBooleanField(null=True)
    float_value = models.FloatField(null=True)
    int_value = models.IntegerField(null=True)
    text_value = models.TextField(null=True)
    datetime_value = models.DateTimeField(null=True)

    class Meta:
        abstract = True

    def set(self, value, value_type='text'):
        if value_type == 'float':
            self.float_value = float(value)
        elif value_type == 'text':
            self.text_value = unicode(value)
        elif value_type == 'int':
            self.int_value = int(value)
        elif value_type == 'bool':
            self.bool_value = bool(value)
        elif value_type == 'date':
            self.datetime_value = datetime(value)
        else:
            raise Exception("Values of type '{0}' aren't supported by MetaInfoValue".format(value_type))
    
    def __str__(self):
        return self.value()

    def value(self):
        result = None
        if self.float_value:
            result = self.float_value
        if self.text_value:
            if result: raise Exception("MetaInfoValues cannot be of more than one type.")
            result = self.text_value
        if self.int_value:
            if result: raise Exception("MetaInfoValues cannot be of more than one type.")
            result = self.int_value
        if self.bool_value:
            if result: raise Exception("MetaInfoValues cannot be of more than one type.")
            result = self.bool_value
        if self.datetime_value:
            if result: raise Exception("MetaInfoValues cannot be of more than one type.")
            result = self.datetime_value
        return result

    def type(self):
        type = None
        if self.float_value:
            type = 'float'
        if self.text_value:
            if type: raise Exception("MetaInfoValues cannot be of more than one type.")
            type = 'text'
        if self.int_value:
            if type: raise Exception("MetaInfoValues cannot be of more than one type.")
            type = 'int'
        if self.bool_value:
            if type: raise Exception("MetaInfoValues cannot be of more than one type.")
            type = 'bool'
        if self.datetime_value:
            if type: raise Exception("MetaInfoValues cannot be of more than one type.")
            type = 'datetime'
        return type

class DatasetMetaInfo(MetaInfo):
    pass

class DatasetMetaInfoValue(MetaInfoValue):
    info_type = models.ForeignKey(DatasetMetaInfo, related_name='values')
    dataset = models.ForeignKey(Dataset, related_name='metainfovalues')

class AnalysisMetaInfo(MetaInfo):
    pass

class AnalysisMetaInfoValue(MetaInfoValue):
    info_type = models.ForeignKey(AnalysisMetaInfo, related_name='values')
    analysis = models.ForeignKey(Analysis, related_name='metainfovalues')

class TopicMetaInfo(MetaInfo):
    pass

class TopicMetaInfoValue(MetaInfoValue):
    info_type = models.ForeignKey(TopicMetaInfo, related_name='values')
    topic = models.ForeignKey(Topic, related_name='metainfovalues')

class DocumentMetaInfo(MetaInfo):
    pass

class DocumentMetaInfoValue(MetaInfoValue):
    info_type = models.ForeignKey(DocumentMetaInfo, related_name='values')
    document = models.ForeignKey(Document, related_name='metainfovalues')

    def __unicode__(self):
        return '[%s(%s)=%s]' % (self.info_type.name, self.document.filename, self.value())

class WordTypeMetaInfo(MetaInfo):
    pass

class WordTypeMetaInfoValue(MetaInfoValue):
    info_type = models.ForeignKey(WordTypeMetaInfo, related_name='values')
    word_type = models.ForeignKey(WordType, related_name='metainfovalues')

class WordTokenMetaInfo(MetaInfo):
    pass

class WordTokenMetaInfoValue(MetaInfoValue):
    info_type = models.ForeignKey(WordTokenMetaInfo, related_name='values')
    word_token = models.ForeignKey(WordToken, related_name='metainfovalues')
    analysis = models.ForeignKey(Analysis, null=True)
















###################################################################
# The Following are unused at the time of this comment.
# Move code above if it becomes used or delete it if it is useless.
###################################################################

## Favorites
class Favorite(models.Model):
    session_key = models.CharField(max_length=40, db_index=True)
    timestamp = models.DateTimeField(default=datetime.now)

    class Meta:
        abstract = True

class DatasetFavorite(Favorite):
    dataset = models.ForeignKey(Dataset)

class AnalysisFavorite(Favorite):
    analysis = models.ForeignKey(Analysis)

class TopicFavorite(Favorite):
    topic = models.ForeignKey(Topic)

class DocumentFavorite(Favorite):
    document = models.ForeignKey(Document)

class ViewFavorite(Favorite):
    '''A unique identifier. For URLs.'''
    favid = models.SlugField(primary_key=True)

    '''A short, human-readable name'''
    name = models.TextField(max_length=128)

    '''Serialization of the filter set'''
    filters = models.TextField()

    class Meta:
        abstract = True

class TopicViewFavorite(ViewFavorite):
    '''The topic we'll be viewing'''
    topic = models.ForeignKey(Topic)

class DocumentViewFavorite(ViewFavorite):
    '''The document we'll be viewing'''
    document = models.ForeignKey(Document)

    '''And the analysis we're using'''
    analysis = models.ForeignKey(Analysis)

'''We want to go through the WordTokenTopis table for the foreignkey, to
optimize queries in the attributes tab'''
## Links between the basic things in the database
#################################################
#
#class AttributeValueDocument(models.Model):
#    document = models.ForeignKey(Document)
#    attribute = models.ForeignKey(Attribute)
#    value = models.ForeignKey(Value)
#
#    def __unicode__(self):
#        return u'{a} is "{v}" for {d}'.format(a=self.attribute, v=self.value,
#                d=self.document)
#
#
#class AttributeValue(models.Model):
#    attribute = models.ForeignKey(Attribute)
#    value = models.ForeignKey(Value)
#    token_count = models.IntegerField(default=0)
#
#
#class AttributeValueWord(models.Model):
#    attribute = models.ForeignKey(Attribute)
#    word = models.ForeignKey(Word)
#    value = models.ForeignKey(Value)
#    count = models.IntegerField(default=0)
#
