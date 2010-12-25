#!/usr/bin/env python

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


from django import forms


# Methods
#########

def sort_topics(topics, sort_by):
    # Because of the way I had to implement metric sorting, and the way that
    # filtering is implemented, you cannot filter after you have sorted.  Be
    # sure to call this method after filtering, and before paginate_list,
    # unless you really know what you are doing.
    django_orderings = ['total_count', '-total_count', 'number', '-number',
            'name', '-name']
    if sort_by in django_orderings:
        return topics.order_by(sort_by)
    elif 'metric:' in sort_by:
        metric_name = sort_by[7:]
        topic_list = list(topics.all())
        topic_list.sort(key=lambda x:
                -x.topicmetricvalue_set.get(metric__name=metric_name).value)
        return topic_list
    else:
        raise ValueError("We don't current support ordering by %s" % sort_by)


def top_values_for_attr_topic(analysis, topic, attribute, order_by='count',
        number=10):
    attrvaltopics = attribute.attributevaluetopic_set.filter(
            topic__analysis=analysis, topic=topic).order_by('-count')
    values = []
    if order_by == 'count':
        attrvaltopics = attrvaltopics[:number]
    for attrvaltopic in attrvaltopics:
        value = attrvaltopic.value
        total_count = attribute.attributevalue_set.get(value=value).token_count
        count = attrvaltopic.count
        percent = float(count) / total_count
        values.append(ValueListing(value.value, count, percent))
    if order_by == 'percent':
        values.sort(key=lambda x: -x.percent)
    return values[:number]


# Classes
#########

class SortTopicForm(forms.Form):
    def __init__(self, analysis, *args, **kwargs):
        super(SortTopicForm, self).__init__(*args, **kwargs)
        choices = []
        choices.append(('name', 'Name'))
        choices.append(('number', 'Number'))
        for metric in analysis.topicmetric_set.all():
            choices.append(('metric:%s' % metric.name, metric.name))
        self.fields['sort'] = forms.ChoiceField(choices, label='Sort by')
        self.fields['sort'].widget.attrs['onchange'] = 'sort_topics()'


class RenameForm(forms.Form):
    def __init__(self, topic_name, *args, **kwargs):
        super(RenameForm, self).__init__(*args, **kwargs)
        self.fields['topic_name'] = forms.CharField(
                widget=forms.TextInput(attrs={'size':'50'}),
                max_length=100,
                initial=topic_name,
                label='')
        self.fields['topic_name'].widget.attrs['onchange'] = 'rename_topic()'


class ValueListing(object):
    def __init__(self, value, count, percent):
        self.value = value
        self.count = count
        self.percent = percent


# vim: et sw=4 sts=4
