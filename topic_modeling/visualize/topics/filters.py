#!/usr/bin/env python

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


from django import forms
from django.db.models import Max, Min

from topic_modeling.visualize import sess_key
from topic_modeling.visualize.models import Document
from topic_modeling.visualize.topics.common import sort_topics
from topic_modeling.visualize.common.ui import FilterForm
from topic_modeling.visualize.common.helpers import paginate_list

# Methods
#########

def possible_topic_filters(analysis):
    possible_filters = [('None', '-------')]
    possible_filters.append(('attribute', 'Attribute'))
    possible_filters.append(('metric', 'Metric'))
    possible_filters.append(('document', 'Document'))
    possible_filters.append(('word', 'Word'))
    return possible_filters


def get_topic_filter_by_name(name):
    if name == 'attribute':
        return TopicFilterByAttribute
    if name == 'metric':
        return TopicFilterByMetric
    if name == 'document':
        return TopicFilterByDocument
    if name == 'word':
        return TopicFilterByWord
    raise ValueError('There is no topic filter with the name %s' % name)


def filter_topics(topics, filters):
    analysis = topics.all()[0].analysis
    filter_form = FilterForm(possible_topic_filters(analysis))
    id = 0
    for filter in filters:
        filter.id = id
        id += 1
        filter_form.add_filter(filter)
        topics = filter.apply(topics)
    return topics, filter_form


def clean_topics_from_session(dataset, topics, session, extra_filters=[], topic=None):
    # This method takes an original list of topics, then filters, sorts, and
    # paginates them from the given session object.  If topic is given, we find
    # the page for that topic
    filters = session.get(sess_key(dataset,'topic-filters'), [])
    topics, filter_form = filter_topics(topics, filters)
    for filter in extra_filters:
        topics = filter.apply(topics)
    sort_by = session.get(sess_key(dataset,'topic-sort'), 'name')
    topics = sort_topics(topics, sort_by, session)
    session[sess_key(dataset,'topics-list')] = topics
    page_num = session.get(sess_key(dataset,'topic-page'), 1)
    per_page = session.get('topics-per-page', 20)
    topics, num_pages, page_num = paginate_list(topics, page_num, per_page, topic)
    session[sess_key(dataset,'topic-page')] = page_num
    return topics, filter_form, num_pages


# Classes
#########

class TopicFilterByAttribute(object):
    def __init__(self, analysis, id):
        self.analysis = analysis
        self.id = id
        self.current_attribute = None
        self.current_value = None
        self.remake_form()

    def apply(self, topic_set):
        if not self.current_attribute or not self.current_value:
            return topic_set
        attr = self.analysis.dataset.attribute_set.get(
                name=self.current_attribute)
        value = attr.value_set.get(value=self.current_value)
        return topic_set.filter(
                attributevaluetopic__attribute=attr,
                attributevaluetopic__value=value)

    def remake_form(self):
        if self.current_attribute:
            attribute = self.current_attribute
        else:
            attribute = 'None'
        if self.current_value:
            value = self.current_value
        else:
            value = 'None'
        self._form = AttributeValueForm(self.analysis.dataset, self.id,
                attribute, value)

    def form(self):
        # This BoundField business is a bit of a hack to just get the part of
        # the HTML that I want.  I could build the HTML for it myself, but this
        # was a little easier.
        ret_val = '<td>Attribute:'
        attr = forms.forms.BoundField(self._form,
                self._form.fields['attribute'], 'attribute_filter_%d' % self.id)
        ret_val += '</td><td>'
        ret_val += attr.as_widget()
        if self.current_attribute:
            val = forms.forms.BoundField(self._form, self._form.fields['value'],
                    'attribute_filter_value_%d' % self.id)
            ret_val += val.as_widget()
        ret_val += '</td><td class="remove">X</td>'
        return ret_val


class AttributeValueForm(forms.Form):
    # This really should be a nested class of TopicFilterByAttribute, but you
    # can't pickle nested classes...
    def __init__(self, dataset, id, attribute, value, *args, **kwargs):
        super(AttributeValueForm, self).__init__(*args, **kwargs)
        attribute_choices = [('None', 'All')]
        attributes = dataset.attribute_set.all()
        for a in attributes:
            attribute_choices.append((a.name, a.name))
        self.fields['attribute'] = forms.ChoiceField(attribute_choices,
                label='Attribute', initial=attribute)
        self.fields['attribute'].widget.attrs['onchange'] = \
                'update_attr_filter_attribute(%d)' % id
        if attribute != 'None':
            attribute = dataset.attribute_set.get(name=attribute)
            value_choices = [('None', 'All')]
            values = attribute.value_set.all()
            for v in values:
                value_choices.append((v.value, v.value))
            self.fields['value'] = forms.ChoiceField(value_choices,
                    label='Value', initial=value)
            self.fields['value'].widget.attrs['onchange'] = \
                    'update_attr_filter_value(%d)' % id


class TopicFilterByMetric(object):
    def __init__(self, analysis, id):
        self.analysis = analysis
        self.id = id
        self.current_metric = None
        self.current_comparator = 'gt'
        self.current_value = None
        self.remake_form()

    def apply(self, topic_set):
        if not self.current_metric:
            return topic_set
        if self.current_comparator == 'gt':
            return topic_set.filter(
                    topicmetricvalue__metric__name=self.current_metric,
                    topicmetricvalue__value__gt=self.current_value)
        if self.current_comparator == 'lt':
            return topic_set.filter(
                    topicmetricvalue__metric__name=self.current_metric,
                    topicmetricvalue__value__lt=self.current_value)
        raise ValueError('Current comparator is not supported: %s' %
                self.current_comparator)

    def remake_form(self):
        if self.current_metric:
            metric = self.current_metric
        else:
            metric = 'None'
        comparator = self.current_comparator
        if self.current_value:
            value = self.current_value
        else:
            value = 'None'
        self._form = MetricForm(self.analysis, self.id, metric, comparator,
                value)
        if not self.current_value:
            self.current_value = self._form.min_value

    def form(self):
        # This BoundField business is a bit of a hack to just get the part of
        # the HTML that I want.  I could build the HTML for it myself, but this
        # was a little easier.
        ret_val = '<td>Metric:'
        metric = forms.forms.BoundField(self._form,
                self._form.fields['metric'], 'metric_filter_%d' % self.id)
        ret_val += '</td><td>'
        ret_val += metric.as_widget()
        if self.current_metric:
            comp = forms.forms.BoundField(self._form, self._form.fields['comp'],
                    'metric_filter_comp_%d' % self.id)
            ret_val += comp.as_widget()
            val = forms.forms.BoundField(self._form, self._form.fields['value'],
                    'metric_filter_value_%d' % self.id)
            ret_val += val.as_widget()
        ret_val += '</td><td class="remove">X</td>'
        return ret_val


class MetricForm(forms.Form):
    # Also should be a nested class...
    def __init__(self, analysis, id, metric, comparator, value, *args,
            **kwargs):
        super(MetricForm, self).__init__(*args, **kwargs)
        # Build the select box for metrics
        self.min_value = None
        metric_choices = [('None', '-------')]
        for m in analysis.topicmetrics.all():
            metric_choices.append((m.name, m.name))
        self.fields['metric'] = forms.ChoiceField(metric_choices,
                label='Metric', initial=metric)
        self.fields['metric'].widget.attrs['onchange'] = \
                'update_metric_filter_metric(%d)' % id
        if metric != 'None':
            # Build the select box for comparators
            comparator_choices = [('gt', 'Greater than'), ('lt', 'Less than')]
            self.fields['comp'] = forms.ChoiceField(comparator_choices,
                    label='', initial=comparator)
            self.fields['comp'].widget.attrs['onchange'] = \
                    'update_metric_filter(%d)' % id
            # Build the select box for values
            metric = analysis.topicmetrics.get(name=metric)
            max_value = metric.topicmetricvalues.aggregate(
                    Max('value'))['value__max']
            min_value = metric.topicmetricvalues.aggregate(
                    Min('value'))['value__min']
            if value == 'None':
                value = min_value
            self.min_value = min_value
            num_choices = 10
            step_size = (max_value - min_value) / (num_choices - 1)
            value_choices = []
            for i in range(num_choices):
                v = min_value + i * step_size
                value_choices.append((v, v))
            self.fields['value'] = forms.ChoiceField(value_choices,
                    label='', initial=value)
            self.fields['value'].widget.attrs['onchange'] = \
                    'update_metric_filter(%d)' % id


class TopicFilterByDocument(object):
    def __init__(self, analysis, id):
        self.analysis = analysis
        self.id = id
        self.current_document_id = None
        self.remake_form()

    def apply(self, topic_set):
        if not self.current_document_id:
            return topic_set
        doc = Document.objects.get(pk=self.current_document_id)
        return topic_set.filter(documenttopic__document=doc)

    def remake_form(self):
        if self.current_document_id:
            document_id = self.current_document_id
        else:
            document_id = 'None'
        self._form = DocumentForm(self.analysis.dataset, self.id, document_id)

    def form(self):
        # This BoundField business is a bit of a hack to just get the part of
        # the HTML that I want.  I could build the HTML for it myself, but this
        # was a little easier.
        ret_val = '<td>Document:'
        document = forms.forms.BoundField(self._form,
                self._form.fields['document'], 'document_filter_%d' % self.id)
        ret_val += '</td><td>'
        ret_val += document.as_widget()
        ret_val += '</td><td class="remove">X</td>'
        return ret_val


class DocumentForm(forms.Form):
    # Also should be a nested class...
    def __init__(self, dataset, id, document, *args, **kwargs):
        super(DocumentForm, self).__init__(*args, **kwargs)
        document_choices = [('None', '-------')]
        for d in dataset.documents.all():
            document_choices.append((d.id, d.filename))
        self.fields['document'] = forms.ChoiceField(document_choices,
                label='Document', initial=document)
        self.fields['document'].widget.attrs['onchange'] = \
                'update_document_filter_document(%d)' % id


class TopicFilterByWord(object):
    def __init__(self, analysis, id):
        self.analysis = analysis
        self.id = id
        self.current_word_type = None
        self.remake_form()

    def apply(self, topic_set):
        if not self.current_word_type:
            return topic_set
        return topic_set.filter(tokens__type=self.current_word_type)
#        word = self.analysis.dataset.word_set.get(type=self.current_word)
#        return topic_set.filter(topicword__word=word)

    def remake_form(self):
        if self.current_word_type:
            word = self.current_word_type
        else:
            word = 'None'
        self._form = WordForm(self.analysis.dataset, self.id, word)

    def form(self):
        # This BoundField business is a bit of a hack to just get the part of
        # the HTML that I want.  I could build the HTML for it myself, but this
        # was a little easier.
        ret_val = '<td>Word:'
        word = forms.forms.BoundField(self._form,
                self._form.fields['word'], 'word_filter_%d' % self.id)
        ret_val += '</td><td>'
        ret_val += word.as_widget()
        ret_val += '</td><td class="remove">X</td>'
        return ret_val


class WordForm(forms.Form):
    # Also should be a nested class...
    def __init__(self, dataset, id, word, *args, **kwargs):
        super(WordForm, self).__init__(*args, **kwargs)
        word_choices = [('None', '-------')]
        for w in dataset.word_set.all():
            word_choices.append((w.type, w.type))
        self.fields['word'] = forms.ChoiceField(word_choices,
                label='Word', initial=word)
        self.fields['word'].widget.attrs['onchange'] = \
                'update_word_filter_word(%d)' % id




# vim: et sw=4 sts=4
