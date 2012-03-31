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

import random
import time
from datetime import datetime

from django.db import models

from topic_modeling.anyjson import deserialize
from django.db.models.aggregates import Count

##############################################################################
# Tables just to hold information about data and documents
##############################################################################

# Basic things in the database
##############################

# FIXME: readable_name and description should be deprecated in favor of the meta info system
class Describable(models.Model):
    '''A unique identifier. For URLs.'''
    name = models.SlugField(unique=True)
    
    '''A short, human-readable name'''
    readable_name = models.TextField(max_length=128)
    
    '''A longer, human-readable description'''
    description = models.TextField()
    
    class Meta:
        abstract = True

class Dataset(Describable):
    dataset_dir = models.CharField(max_length=128, db_index=True)
    files_dir = models.CharField(max_length=128, db_index=True)
    visible = models.BooleanField(default=True)

    def __unicode__(self):
        return self.name
    
    def delete(self, *args, **kwargs):
        for analysis in self.analyses.all():
            print "\tremove analysis " + str(analysis)
            analysis.delete()
        
        for doc in self.documents.all():
            print "\tremove doc " + str(doc)
            doc.delete()
        
        super(Dataset, self).delete(*args, **kwargs)


LEFT_CONTEXT_SIZE = 40
RIGHT_CONTEXT_SIZE = 40
class Document(models.Model):
    filename = models.CharField(max_length=128, db_index=True)
    dataset = models.ForeignKey(Dataset, related_name='documents')
#    word_count = models.IntegerField(default=0)

    def __unicode__(self):
        return unicode(self.filename)

#    def get_markup(self, analysis):
#        markup_file = MarkupFile.objects.get(document=self, analysis=analysis)
#        markup = deserialize(open(self.dataset.dataset_dir + '/' +
#                markup_file.path).read())
#        return markup

    def get_context_for_word(self, word_to_find, analysis, topic=None):
        markup = self.get_markup(analysis)
        indices = []
        for i, word in enumerate(markup):
            if word['word'] == word_to_find:
                if not topic or word['topic'] == topic:
                    indices.append(i)
        word_index = random.choice(indices)
        word_to_use = markup[word_index]
        text = open(self.dataset.files_dir + '/' +
                self.filename).read().decode('utf-8', 'replace')
        text = text.replace(u'\uFFFD', ' ')
        raw_word = text[word_to_use['start']:word_to_use['start']+len(word_to_find)]
        
        #Right Context
        right_start_position = word_to_use['start'] + len(word_to_find)
        right_end_position = right_start_position
        for word in markup[word_index+1:]:
            new_position = word['start'] + len(word['word'])
            length = new_position - right_start_position
            if length > RIGHT_CONTEXT_SIZE:
                break
            right_end_position = new_position
        right_context = text[right_start_position:right_end_position]
        
        #Left Context
        left_start_position = word_to_use['start']
        left_end_position = left_start_position
        for word in reversed(markup[:word_index]):
            new_position = word['start']
            length = left_start_position - new_position
            if length > LEFT_CONTEXT_SIZE:
                break
            left_end_position = new_position
        left_context = text[left_end_position:left_start_position]
        
        return left_context, raw_word, right_context

    before_text = '<span style="color: blue;">'
    after_text = '</span>'
    def get_highlighted_text(self, topics, analysis):
#        return ''
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
#        markup = self.get_markup(analysis)
#        indices = []
#        for i, word in enumerate(markup):
#            if word['topic'] in topics:
#                indices.append(i)
#        text = open(self.dataset.files_dir + '/' +
#                self.filename).read().decode('utf-8')
#        
#        numchars = len(before_text) + len(after_text)
#        for i, index in enumerate(indices):
#            start_index = markup[index]['start'] + i * numchars
#            end_index = start_index + len(markup[index]['word'])
#            word = text[start_index:end_index]
#            text = text[:start_index] + before_text + word + after_text + \
#                    text[end_index:]
#        return text

    def text(self, kwic=None):
        text = open(self.dataset.files_dir + "/" +
                    self.filename, 'r').read().decode('utf-8')
        if kwic:
            beg_context, end_context = self.get_kwic_context_ends(kwic, text)
            if beg_context >= 0:
                text = text[:beg_context] + \
                        '<span style=\"text-decoration: underline;\">' + \
                        text[beg_context:end_context] + '</span>' + \
                        text[end_context:]

        text = unicode(text)
        text = text.replace(' ;', ';')
        text = text.replace(' .', '.')
        text = text.replace(' ,', ',')
        text = text.replace(' )', ')')
        text = text.replace('( ', '(')
        text = text.replace(' !', '!')
        text = text.replace(' :', ':')

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

    class Meta:
        ordering = ['dataset', 'filename']


class WordType(models.Model):
    type = models.CharField(max_length=128, db_index=True) #@ReservedAssignment

class WordToken(models.Model):
    type = models.ForeignKey(WordType, related_name='tokens') #@ReservedAssignment
    document = models.ForeignKey(Document, related_name='tokens')
    token_index = models.IntegerField()
    start = models.IntegerField()
    
#    '''The form of this type instance. If null, it defers to type.value'''
#    token = models.CharField(max_length=128, db_index=True, null=True)
    topics = models.ManyToManyField('Topic', related_name='tokens')
    
    def __unicode__(self):
        return '[%s,%s]' % (self.type.type, self.token_index)

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

##############################################################################
# Tables that hold information about particular analyses of the data
##############################################################################

# Basic components of the analysis
##################################

# This is assuming perhaps several different runs of different kinds of LDA
class Analysis(models.Model):
    dataset = models.ForeignKey(Dataset, related_name='analyses')
    stopwords = models.ManyToManyField(WordToken)

    name = models.SlugField()

    '''A short, human-readable name'''
    readable_name = models.TextField(max_length=128)

    '''A longer, human-readable description'''
    description = models.TextField()

    def __unicode__(self):
        return self.name
    
    def delete(self, *args, **kwargs):
        for topic in self.topics.all():
            print "\tremove topic " + str(topic)
            topic.delete()
        
        super(Analysis, self).delete(*args, **kwargs)


class MarkupFile(models.Model):
    document = models.ForeignKey(Document)
    analysis = models.ForeignKey(Analysis)
    path = models.CharField(max_length=128)


class Topic(models.Model):
    number = models.IntegerField()
#    name = models.CharField(max_length=128)
#    total_count = models.IntegerField()
    analysis = models.ForeignKey(Analysis, related_name='topics')
#    documents = models.ManyToManyField(Document, through='DocumentTopic')
    metrics = models.ManyToManyField('TopicMetric', through='TopicMetricValue')
#    words = models.ManyToManyField(Word, through='TopicWord')

    def __unicode__(self):
        return '%d: %s' % (self.number, self.name)

#    class Meta:
#        ordering = ['name']
    
    def total_count(self):
        return self.tokens.count()
    
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


class TopicGroup(Topic):
    @property
    def subtopics(self):
        return [topicgrouptopic.topic for topicgrouptopic
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

### Metrics ###
class Metric(models.Model):
    name = models.CharField(max_length=128)
    class Meta:
        abstract = True

class PairwiseMetric(Metric):
    pass
    class Meta:
        abstract = True

class MetricValue(models.Model):
    value = models.FloatField()
    class Meta:
        abstract = True

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
        return '%s(%s, %s) = %d' % (self.metric.name, self.topic1.name,
                self.topic2.name, self.value)

# These could go under the dataset section, but there are some metrics that
# only make sense with a corresponding Analysis, so we will just put them all
# in the same class here, even if some of the metrics ignore the analysis.
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

# Metadata

# TODO: rename MetaInfo -> MetaInfoField
# TODO: also rename children
# TODO: keep track of the field type. Use the 'choices' parameter to specify possible types.
# TODO: Update the set, value, and type methods
class MetaInfo(models.Model):
    name = models.CharField(max_length=128, db_index=True)
    
    class Meta:
        abstract = True

# TODO: Use a consistent related_name in the children of this model.
# TODO: Create class MetaInfoTarget with a value method that references the consistent metainfo related_name
class MetaInfoValue(models.Model):
    bool_value = models.NullBooleanField(null=True)
    float_value = models.FloatField(null=True)
    int_value = models.IntegerField(null=True)
    text_value = models.TextField(null=True)
    datetime_value = models.DateTimeField(null=True)
    
    class Meta:
        abstract = True
    
    def set(self, value):
        if isinstance(value, float):
            self.float_value = value
        elif isinstance(value, basestring):
            self.text_value = value
        elif isinstance(value, int):
            self.int_value = value
        elif isinstance(value, bool):
            self.bool_value = value
        elif isinstance(value, datetime):
            self.datetime_value = value
        elif isinstance(value, time.struct_time):
            self.datetime_value = datetime(*value[0:6])
        else:
            raise Exception("Values of type '{0}' aren't supported by MetaInfoValue".format(type(value)))
    
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

# vim: et sw=4 sts=4
