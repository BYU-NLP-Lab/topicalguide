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


from django.http import HttpResponse
from django.utils import simplejson

from topic_modeling.visualize.common import FilterForm
from topic_modeling.visualize.common import paginate_list
from topic_modeling.visualize.models import Analysis
from topic_modeling.visualize.models import Attribute
from topic_modeling.visualize.models import Topic
from topic_modeling.visualize.models import TopicName
from topic_modeling.visualize.models import TopicNameScheme
from topic_modeling.visualize.topics.common import top_values_for_attr_topic
from topic_modeling.visualize.topics.filters import clean_topics_from_session
from topic_modeling.visualize.topics.filters import get_topic_filter_by_name
from topic_modeling.visualize.topics.filters import possible_topic_filters

# General and Sidebar stuff
###########################

def rename_topic(request, dataset, analysis, topic, name):
    topic = Topic.objects.get(analysis__dataset__name=dataset,
            analysis__name=analysis, number=topic)
    topic.name = name
    topic.save()
    return HttpResponse(topic.name)


def topic_ordering(request, dataset, analysis, order_by):
    request.session['topic-sort'] = order_by
    request.session['topic-page'] = 1
    name_scheme_id = request.session['current_name_scheme_id']
    ret_val = dict()
    topics = Topic.objects.filter(analysis__name=analysis,
            analysis__dataset__name=dataset)
    topics, _, num_pages = clean_topics_from_session(topics, request.session)
    ret_val['topics'] = [vars(AjaxTopic(topic, get_topic_name(topic, name_scheme_id))) for topic in topics]
    ret_val['num_pages'] = num_pages
    ret_val['page'] = 1
    return HttpResponse(simplejson.dumps(ret_val))


def get_topic_page(request, dataset, analysis, topic, number):
    request.session['topic-page'] = int(number)
    name_scheme_id = request.session['current_name_scheme_id']
    ret_val = dict()
    topics = request.session.get('topics-list', None)
    if not topics:
        topics = Topic.objects.filter(analysis__name=analysis,
                analysis__dataset__name=dataset)
    num_per_page = request.session.get('topics-per-page', 20)
    page = int(number)
    topics, num_pages, _ = paginate_list(topics, page, num_per_page)
    ret_val['topics'] = [vars(AjaxTopic(topic, get_topic_name(topic, name_scheme_id))) for topic in topics]
    ret_val['num_pages'] = num_pages
    ret_val['page'] = page
    return HttpResponse(simplejson.dumps(ret_val))


# Widgets
#########

def top_attrvaltopic(request, dataset, analysis, topic, attribute, order_by):
    ret_val = dict()
    request.session['topic-attribute'] = attribute
    attribute = Attribute.objects.get(dataset__name=dataset, name=attribute)
    analysis = Analysis.objects.get(dataset__name=dataset, name=analysis)
    topic = analysis.topic_set.get(number=topic)
    top_values = top_values_for_attr_topic(analysis, topic, attribute, order_by)
    ret_val['attribute'] = attribute.name
    ret_val['values'] = [vars(v) for v in top_values]
    return HttpResponse(simplejson.dumps(ret_val))


def similar_topics(request, dataset, analysis, topic, measure):
    name_scheme_id = request.session['current_name_scheme_id']
    ret_val = dict()
    request.session['topic-similarity-measure'] = measure
    analysis = Analysis.objects.get(dataset__name=dataset, name=analysis)
    topic = analysis.topic_set.get(number=topic)
    topic_name = get_topic_name(topic, name_scheme_id)
    measure = analysis.pairwisetopicmetric_set.get(name=measure)
    similar_topics = topic.pairwisetopicmetricvalue_originating.\
            select_related().filter(metric=measure).order_by('-value')[1:11]
    topics = [t.topic2 for t in similar_topics]
    values = [t.value for t in similar_topics]
    ret_val['values'] = values
    ret_val['topics'] = [vars(AjaxTopic(topic, topic_name)) for topic in topics]
    return HttpResponse(simplejson.dumps(ret_val))


# Filters
#########

def new_topic_filter(request, dataset, analysis, topic, name):
    analysis = Analysis.objects.get(dataset__name=dataset, name=analysis)
    filters = request.session.get('topic-filters', [])
    filter_form = FilterForm(possible_topic_filters(analysis))
    id = 0
    for filter in filters:
        filter.id = id
        filter_form.add_filter(filter)
        id += 1
    new_filter = get_topic_filter_by_name(name)(analysis, id)
    filter_form.add_filter(new_filter)
    filters.append(new_filter)
    request.session['topic-filters'] = filters
    return HttpResponse(filter_form.__unicode__())


def remove_topic_filter(request, dataset, analysis, topic, number):
    request.session['topic-filters'].pop(int(number))
    request.session.modified = True
    return filtered_topics_response(request, dataset, analysis)


def filtered_topics_response(request, dataset, analysis):
    name_scheme_id = request.session['current_name_scheme_id']
    analysis = Analysis.objects.get(dataset__name=dataset, name=analysis)
    topics = analysis.topic_set
    request.session['topic-page'] = 1
    topics, filter_form, num_pages = clean_topics_from_session(topics,
            request.session)
    ret_val = dict()
    ret_val['filter_form'] = filter_form.__unicode__()
    ret_val['topics'] = [vars(AjaxTopic(topic, get_topic_name(topic, name_scheme_id))) for topic in topics]
    ret_val['num_pages'] = num_pages
    ret_val['page'] = request.session.get('topic-page', 1)
    return HttpResponse(simplejson.dumps(ret_val))


def update_topic_attribute_filter(request, dataset, analysis, topic, number,
        attribute, value=None):
    filter = request.session['topic-filters'][int(number)]
    if attribute == 'None':
        filter.current_attribute = None
    else:
        filter.current_attribute = attribute
    if value == 'None':
        filter.current_value = None
    else:
        filter.current_value = value
    filter.remake_form()
    request.session.modified = True
    return filtered_topics_response(request, dataset, analysis)


def update_topic_metric_filter(request, dataset, analysis, topic, number,
        metric, comp=None, value=None):
    filter = request.session['topic-filters'][int(number)]
    if metric == 'None':
        filter.current_metric = None
    else:
        filter.current_metric = metric
    if comp:
        filter.current_comparator = comp
    if value:
        filter.current_value = value
    filter.remake_form()
    request.session.modified = True
    return filtered_topics_response(request, dataset, analysis)


def update_topic_document_filter(request, dataset, analysis, topic, number,
        document):
    filter = request.session['topic-filters'][int(number)]
    if document == 'None':
        filter.current_document_id = None
    else:
        filter.current_document_id = document
    filter.remake_form()
    request.session.modified = True
    return filtered_topics_response(request, dataset, analysis)


def update_topic_word_filter(request, dataset, analysis, topic, number, word):
    filter = request.session['topic-filters'][int(number)]
    if word == 'None':
        filter.current_word = None
    else:
        filter.current_word = word
    filter.remake_form()
    request.session.modified = True
    return filtered_topics_response(request, dataset, analysis)

def get_topic_name(topic, name_scheme_id):
    ns = TopicNameScheme.objects.get(id=name_scheme_id)
    return str(topic.number) + ": " + TopicName.objects.get(topic=topic,name_scheme=ns).name

class AjaxTopic(object):
    def __init__(self, topic, topic_name):
        self.name = topic_name
        self.number = topic.number


# vim: et sw=4 sts=4
