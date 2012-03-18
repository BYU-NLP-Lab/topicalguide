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
from django.db.models import Min, Max

from topic_modeling.visualize import sess_key
from topic_modeling.visualize.common.ui import FilterForm
from topic_modeling.visualize.common.helpers import paginate_list
from topic_modeling.visualize.documents.common import sort_documents

# Methods
#########

# Filtering/sorting methods

def possible_document_filters():
    possible_filters = [('None', 'Filter by...'),
                        ('topic', '...Topic'),
                        ('attribute', '...Attribute'),
                        ('metric', '...Metric')]
    return possible_filters


def get_doc_filter_by_name(name):
    if name == 'topic':
        return DocumentFilterByTopic
    if name == 'attribute':
        return DocumentFilterByAttribute
    if name == 'metric':
        return DocumentFilterByMetric
    raise ValueError('There is no topic filter with the name %s' % name)


def clean_docs_from_session(documents, session, doc=None):
    # This method takes an original list of documents, then filters, sorts, and
    # paginates them from the given session object.
    
    dataset = documents[0].dataset
    filters = session.get(sess_key(dataset,'document-filters'), [])
    documents, filter_form = filter_documents(documents, filters)
    sort_by = session.get(sess_key(dataset,'document-sort'), 'filename')
    documents = sort_documents(documents, sort_by)
    
    page_num = session.get(sess_key(dataset,'document-page'), 1)
    per_page = session.get('documents-per-page', 20)
    docs, num_pages, page_num = paginate_list(documents, page_num, per_page, doc)
    session[sess_key(dataset,'document-page')] = page_num
    return docs, filter_form, num_pages


def filter_documents(documents, filters):
    filter_form = FilterForm(possible_document_filters())
    id = 0
    for filter in filters:
        filter.id = id
        id += 1
        filter_form.add_filter(filter)
        documents = filter.apply(documents)
    return documents, filter_form


# Classes
#########

class DocumentFilterByTopic(object):
    def __init__(self, dataset, analysis, id):
        self.dataset = dataset
        self.analysis = analysis
        self.current_topic = None
        self.id = id
        self.remake_form()

    def apply(self, document_set):
        if not self.current_topic:
            return document_set
        topic = self.analysis.topics.get(number=self.current_topic)
        return document_set.filter(documenttopic__topic=topic)

    def remake_form(self):
        if self.current_topic:
            topic = self.current_topic
        else:
            topic = 'None'
        self._form = DocumentFilterByTopicForm(self.analysis, self.id, topic)

    def form(self):
        # Used to the BoundField yet?
        ret_val = '<td>Topic:'
        topic = forms.forms.BoundField(self._form,
                self._form.fields['topic'], 'topic_filter_%d' % self.id)
        ret_val += '</td><td>'
        ret_val += topic.as_widget()
        ret_val += '</td><td class="remove">X</td>'
        return ret_val


class DocumentFilterByTopicForm(forms.Form):
    # Should be nested...
    def __init__(self, analysis, id, topic, *args, **kwargs):
        super(DocumentFilterByTopicForm, self).__init__(*args, **kwargs)
        topics = [(str(t.number), t.name) for t in analysis.topics.all()]
        topics = [('None', 'All')] + topics
        self.fields['topic'] = forms.ChoiceField(topics, label='Topic',
                initial=topic)
        self.fields['topic'].widget.attrs["onchange"] = \
                "update_topic_filter(%d)" % id


class DocumentFilterByAttribute(object):
    def __init__(self, dataset, analysis, id):
        self.dataset = dataset
        self.analysis = analysis
        self.id = id
        self.current_attribute = None
        self.current_value = None
        self.remake_form()

    def apply(self, document_set):
        if not self.current_attribute or not self.current_value:
            return document_set
        attr = self.dataset.attribute_set.get(name=self.current_attribute)
        value = attr.value_set.get(value=self.current_value)
        return document_set.filter(
                attributevaluedocument__attribute=attr,
                attributevaluedocument__value=value)

    def remake_form(self):
        if self.current_attribute:
            attribute = self.current_attribute
        else:
            attribute = 'None'
        if self.current_value:
            value = self.current_value
        else:
            value = 'None'
        self._form = AttributeValueForm(self.dataset, self.id, attribute,
                value)

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
    # This really should be a nested class of DocumentFilterByAttribute, but
    # you can't pickle nested classes...
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


class DocumentFilterByMetric(object):
    def __init__(self, dataset, analysis, id):
        self.dataset = dataset
        self.analysis = analysis
        self.id = id
        self.current_metric = None
        self.current_comparator = 'gt'
        self.current_value = None
        self.remake_form()

    def apply(self, document_set):
        if not self.current_metric:
            return document_set
        if self.current_comparator == 'gt':
            return document_set.filter(
                    documentmetricvalue__metric__name=self.current_metric,
                    documentmetricvalue__value__gt=self.current_value)
        if self.current_comparator == 'lt':
            return document_set.filter(
                    documentmetricvalue__metric__name=self.current_metric,
                    documentmetricvalue__value__lt=self.current_value)
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
        for m in analysis.documentmetric_set.all():
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
            metric = analysis.documentmetric_set.get(name=metric)
            max_value = metric.documentmetricvalue_set.aggregate(
                    Max('value'))['value__max']
            min_value = metric.documentmetricvalue_set.aggregate(
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


# vim: et sw=4 sts=4
