# The Topic Browser
# Copyright 2010-2011 Brigham Young University
#
# This file is part of the Topic Browser <http://nlp.cs.byu.edu/topic_browser>.
#
# The Topic Browser is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published by the
# Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# The Topic Browser is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public License
# for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with the Topic Browser.  If not, see <http://www.gnu.org/licenses/>.
#
# If you have inquiries regarding any further use of the Topic Browser, please
# contact the Copyright Licensing Office, Brigham Young University, 3760 HBLL,
# Provo, UT 84602, (801) 422-9339 or 422-3821, e-mail copyright@byu.edu.

import random
from django.db import models
from topic_modeling.anyjson import deserialize

##############################################################################
# Tables just to hold information about data and documents
##############################################################################

# Basic things in the database
##############################

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

    def __unicode__(self):
        return self.name


class Document(models.Model):
    filename = models.CharField(max_length=128, db_index=True)
    dataset = models.ForeignKey(Dataset)
    word_count = models.IntegerField(default=0)
    words = models.ManyToManyField('Word', through='DocumentWord')
    attributes = models.ManyToManyField('Attribute',
            through='AttributeValueDocument')

    def __unicode__(self):
        return unicode(self.filename)

    def get_markup(self, analysis):
        markup_file = MarkupFile.objects.get(document=self, analysis=analysis)
        markup = deserialize(open(self.dataset.dataset_dir + '/' +
                markup_file.path).read())
        return markup

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
        # Get right context
        start_index = word_to_use['start'] + len(word_to_find)
        end_index = start_index
        current_index = word_index
        while (current_index < len(markup) and end_index - start_index < 50):
            word = markup[current_index]
            end_index = word['start'] + len(word['word'])
            current_index += 1
        right_context = text[start_index:end_index]
        # Get left context
        end_index = word_to_use['start']
        start_index = end_index
        current_index = word_index
        while (current_index >= 0 and
                end_index - markup[current_index]['start'] < 50):
            start_index = markup[current_index]['start']
            current_index -= 1
        left_context = text[start_index:end_index]
        return right_context, left_context

    def get_highlighted_text(self, topics, analysis):
        markup = self.get_markup(analysis)
        indices = []
        for i, word in enumerate(markup):
            if word['topic'] in topics:
                indices.append(i)
        text = open(self.dataset.files_dir + '/' +
                self.filename).read().decode('utf-8')
        before_text = '<span style="color: blue;">'
        after_text = '</span>'
        numchars = len(before_text) + len(after_text)
        for i, index in enumerate(indices):
            start_index = markup[index]['start'] + i * numchars
            end_index = start_index + len(markup[index]['word'])
            word = text[start_index:end_index]
            text = text[:start_index] + before_text + word + after_text + \
                    text[end_index:]
        return text

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
            return self.attributevaluedocument_set.get(attribute__name='title').value
        except AttributeValueDocument.DoesNotExist:
            return self.filename

    class Meta:
        ordering = ['dataset', 'filename']


class Attribute(models.Model):
    name = models.CharField(max_length=128, db_index=True)
    dataset = models.ForeignKey(Dataset)
    documents = models.ManyToManyField('Document',
            through='AttributeValueDocument')
    # or this?
    # analysis = models.ForeignKey(Analysis)

    def __unicode__(self):
        return self.name

    class Meta:
        ordering = ['name']


class Value(models.Model):
    value = models.CharField(max_length=128, db_index=True)
    attribute = models.ForeignKey(Attribute)

    def __unicode__(self):
        return self.value

    class Meta:
        ordering = ['value']


class Word(models.Model):
    dataset = models.ForeignKey(Dataset)
    count = models.IntegerField(default=0)
    type = models.CharField(max_length=128, db_index=True)
    ngram = models.BooleanField(default=False)

    class Meta:
        ordering = ['type']

    def __unicode__(self):
        return self.type


# Links between the basic things in the database
################################################

class AttributeValueDocument(models.Model):
    document = models.ForeignKey(Document)
    attribute = models.ForeignKey(Attribute)
    value = models.ForeignKey(Value)

    def __unicode__(self):
        return u'{a} is "{v}" for {d}'.format(a=self.attribute, v=self.value,
                d=self.document)


class AttributeValue(models.Model):
    attribute = models.ForeignKey(Attribute)
    value = models.ForeignKey(Value)
    token_count = models.IntegerField(default=0)


class AttributeValueWord(models.Model):
    attribute = models.ForeignKey(Attribute)
    word = models.ForeignKey(Word)
    value = models.ForeignKey(Value)
    count = models.IntegerField(default=0)


class DocumentWord(models.Model):
    document = models.ForeignKey(Document)
    word = models.ForeignKey(Word)
    count = models.IntegerField(default=0)


##############################################################################
# Tables that hold information about particular analyses of the data
##############################################################################

# Basic components of the analysis
##################################

# This is assuming perhaps several different runs of different kinds of LDA
class Analysis(Describable):
    dataset = models.ForeignKey(Dataset)

    def __unicode__(self):
        return self.dataset.name + '-' + self.name


class MarkupFile(models.Model):
    document = models.ForeignKey(Document)
    analysis = models.ForeignKey(Analysis)
    path = models.CharField(max_length=128)


class Topic(models.Model):
    number = models.IntegerField()
    name = models.CharField(max_length=128)
    total_count = models.IntegerField()
    analysis = models.ForeignKey(Analysis)
    documents = models.ManyToManyField(Document, through='DocumentTopic')
    metrics = models.ManyToManyField('TopicMetric', through='TopicMetricValue')
    words = models.ManyToManyField(Word, through='TopicWord')

    def __unicode__(self):
        return '%d: %s' % (self.number, self.name)

    class Meta:
        ordering = ['name']

class TopicGroup(Topic):

    @property
    def subtopics(self):
        return [topicgrouptopic.topic for topicgrouptopic
                in TopicGroupTopic.objects.filter(group=self)]

class TopicGroupTopic(models.Model):
    topic = models.ForeignKey(Topic)
    group = models.ForeignKey(TopicGroup, related_name='group')

class TopicNameScheme(models.Model):
    analysis = models.ForeignKey(Analysis)
    name = models.CharField(max_length=128)

    def __unicode__(self):
        return self.name

class TopicName(models.Model):
    topic = models.ForeignKey(Topic)
    name_scheme = models.ForeignKey(TopicNameScheme)
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
    dataset = models.ForeignKey(Dataset)
    metric = models.ForeignKey(DatasetMetric)

class AnalysisMetric(Metric):
    pass

class AnalysisMetricValue(MetricValue):
    analysis = models.ForeignKey(Analysis)
    metric = models.ForeignKey(AnalysisMetric)

class TopicMetric(Metric):
    analysis = models.ForeignKey(Analysis)

    def __unicode__(self):
        return self.name

class TopicMetricValue(MetricValue):
    topic = models.ForeignKey(Topic)
    metric = models.ForeignKey(TopicMetric)

class PairwiseTopicMetric(PairwiseMetric):
    analysis = models.ForeignKey(Analysis)

    def __unicode__(self):
        return self.name + ': ' + self.analysis.name

class PairwiseTopicMetricValue(MetricValue):
    topic1 = models.ForeignKey(Topic,
            related_name='pairwisetopicmetricvalue_originating')
    topic2 = models.ForeignKey(Topic,
            related_name='pairwisetopicmetricvalue_ending')
    metric = models.ForeignKey(PairwiseTopicMetric)

    def __unicode__(self):
        return '%s(%s, %s) = %d' % (self.metric.name, self.topic1.name,
                self.topic2.name, self.value)

# These could go under the dataset section, but there are some metrics that
# only make sense with a corresponding Analysis, so we will just put them all
# in the same class here, even if some of the metrics ignore the analysis.
class DocumentMetric(Metric):
    analysis = models.ForeignKey(Analysis)

    def __unicode__(self):
        return self.name

class DocumentMetricValue(MetricValue):
    document = models.ForeignKey(Document)
    metric = models.ForeignKey(DocumentMetric)

class PairwiseDocumentMetric(PairwiseMetric):
    analysis = models.ForeignKey(Analysis)

    def __unicode__(self):
        return self.name + ': ' + self.analysis.name

class PairwiseDocumentMetricValue(MetricValue):
    document1 = models.ForeignKey(Document,
            related_name='pairwisedocumentmetricvalue_originating')
    document2 = models.ForeignKey(Document,
            related_name='pairwisedocumentmetricvalue_ending')
    metric = models.ForeignKey(PairwiseDocumentMetric)

    def __unicode__(self):
        return '%s(%s, %s) = %d' % (self.metric.name, self.document1.filename,
                self.document2.filename, self.value)

class WordMetric(Metric):
    analysis = models.ForeignKey(Analysis)

class WordMetricValue(MetricValue):
    word = models.ForeignKey(Word)
    metric = models.ForeignKey(WordMetric)



# Links between the basic components of the analysis and with the raw data
##########################################################################

class TopicWord(models.Model):
    topic = models.ForeignKey(Topic)
    word = models.ForeignKey(Word)
    count = models.IntegerField(default=0)


class DocumentTopic(models.Model):
    topic = models.ForeignKey(Topic)
    document = models.ForeignKey(Document)
    count = models.IntegerField(default=0)


class DocumentTopicWord(models.Model):
    topic = models.ForeignKey(Topic)
    word = models.ForeignKey(Word)
    document = models.ForeignKey(Document)
    count = models.IntegerField(default=0)


class AttributeValueTopic(models.Model):
    attribute = models.ForeignKey(Attribute)
    value = models.ForeignKey(Value)
    topic = models.ForeignKey(Topic)
    count = models.IntegerField(default=0)

# Metadata
class MetaInfo(models.Model):
    name = models.CharField(max_length=128, db_index=True)
    
    class Meta:
        abstract = True

class MetaInfoValue(models.Model):
    bool_value = models.NullBooleanField(null=True)
    float_value = models.FloatField(null=True)
    int_value = models.IntegerField(null=True)
    text_value = models.TextField(null=True)
    
    class Meta:
        abstract = True
    
    def value(self):
        if hasattr(self, 'float_value'):
            return self.float_value
        if hasattr(self, 'text_value'):
            return self.text_value
        if hasattr(self, 'int_value'):
            return self.int_value
        if hasattr(self, 'bool_value'):
            return self.bool_value
        return None

class DatasetMetaInfo(MetaInfo):
    pass

class DatasetMetaInfoValue(MetaInfoValue):
    info_type = models.ForeignKey(DatasetMetaInfo)
    dataset = models.ForeignKey(Dataset)

class AnalysisMetaInfo(MetaInfo):
    pass

class AnalysisMetaInfoValue(MetaInfoValue):
    info_type = models.ForeignKey(AnalysisMetaInfo)
    analysis = models.ForeignKey(Analysis)

class TopicMetaInfo(MetaInfo):
    pass

class TopicMetaInfoValue(MetaInfoValue):
    info_type = models.ForeignKey(TopicMetaInfo)
    topic = models.ForeignKey(Topic)

class DocumentMetaInfo(MetaInfo):
    pass

class DocumentMetaInfoValue(MetaInfoValue):
    info_type = models.ForeignKey(DocumentMetaInfo)
    document = models.ForeignKey(Document)

class WordMetaInfo(MetaInfo):
    pass

class WordMetaInfoValue(MetaInfoValue):
    info_type = models.ForeignKey(WordMetaInfo)
    word = models.ForeignKey(Word)

# vim: et sw=4 sts=4
