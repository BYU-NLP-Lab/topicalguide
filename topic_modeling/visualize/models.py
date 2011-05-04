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

class Dataset(models.Model):
    data_root = models.CharField(max_length=128, db_index=True)
    files_dir = models.CharField(max_length=128, db_index=True)
    name = models.CharField(max_length=128, unique=True, db_index=True)
    description = models.TextField()

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
        markup = deserialize(open(self.dataset.data_root + '/' +
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
        return open(self.dataset.data_root + "/" +
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
class Analysis(models.Model):
    name = models.CharField(max_length=128, db_index=True)
    description = models.TextField()
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


class TopicMetric(models.Model):
    name = models.CharField(max_length=128)
    analysis = models.ForeignKey(Analysis)

    def __unicode__(self):
        return self.name


class PairwiseTopicMetric(models.Model):
    name = models.CharField(max_length=128)
    analysis = models.ForeignKey(Analysis)

    def __unicode__(self):
        return self.name + ': ' + self.analysis.name


class ExtraTopicInformation(models.Model):
    name = models.CharField(max_length=128)
    analysis = models.ForeignKey(Analysis)


# These could go under the dataset section, but there are some metrics that
# only make sense with a corresponding Analysis, so we will just put them all
# in the same class here, even if some of the metrics ignore the analysis.
class DocumentMetric(models.Model):
    name = models.CharField(max_length=128)
    analysis = models.ForeignKey(Analysis)

    def __unicode__(self):
        return self.name


class PairwiseDocumentMetric(models.Model):
    name = models.CharField(max_length=128)
    analysis = models.ForeignKey(Analysis)

    def __unicode__(self):
        return self.name + ': ' + self.analysis.name


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


class TopicMetricValue(models.Model):
    topic = models.ForeignKey(Topic)
    metric = models.ForeignKey(TopicMetric)
    value = models.FloatField()


class PairwiseTopicMetricValue(models.Model):
    topic1 = models.ForeignKey(Topic,
            related_name='pairwisetopicmetricvalue_originating')
    topic2 = models.ForeignKey(Topic,
            related_name='pairwisetopicmetricvalue_ending')
    metric = models.ForeignKey(PairwiseTopicMetric)
    value = models.FloatField()

    def __unicode__(self):
        return '%s(%s, %s) = %d' % (self.metric.name, self.topic1.name,
                self.topic2.name, self.value)


class DocumentMetricValue(models.Model):
    document = models.ForeignKey(Document)
    metric = models.ForeignKey(DocumentMetric)
    value = models.FloatField()


class PairwiseDocumentMetricValue(models.Model):
    document1 = models.ForeignKey(Document,
            related_name='pairwisedocumentmetricvalue_originating')
    document2 = models.ForeignKey(Document,
            related_name='pairwisedocumentmetricvalue_ending')
    metric = models.ForeignKey(PairwiseDocumentMetric)
    value = models.FloatField()

    def __unicode__(self):
        return '%s(%s, %s) = %d' % (self.metric.name, self.document1.name,
                self.document2.name, self.value)


class ExtraTopicInformationValue(models.Model):
    topic = models.ForeignKey(Topic)
    type = models.ForeignKey(ExtraTopicInformation)
    value = models.TextField()


# vim: et sw=4 sts=4
