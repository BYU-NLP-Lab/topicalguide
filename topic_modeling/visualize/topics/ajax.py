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
from django.db.models.aggregates import Min

from topic_modeling.visualize.common import FilterForm
from topic_modeling.visualize.common import paginate_list
from topic_modeling.visualize.models import Analysis, DocumentTopicWord
from topic_modeling.visualize.models import Attribute
from topic_modeling.visualize.models import Topic
from topic_modeling.visualize.models import TopicGroup
from topic_modeling.visualize.models import TopicGroupTopic
from topic_modeling.visualize.models import TopicWord
from topic_modeling.visualize.models import DocumentTopic
from topic_modeling.visualize.models import AttributeValueTopic
from topic_modeling.visualize.topics.common import top_values_for_attr_topic
from topic_modeling.visualize.topics.common import get_topic_name
from topic_modeling.visualize.topics.filters import clean_topics_from_session
from topic_modeling.visualize.topics.filters import get_topic_filter_by_name
from topic_modeling.visualize.topics.filters import possible_topic_filters
import sys
from django.db import transaction

# General and Sidebar stuff
###########################

def rename_topic(request, dataset, analysis, topic, name):
    raise NotImplementedError('This is currently broken')
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
    ret_val['topics'] = [vars(AjaxTopic(topic, get_topic_name(topic,
        name_scheme_id))) for topic in topics]
    ret_val['num_pages'] = num_pages
    ret_val['page'] = 1
    return HttpResponse(simplejson.dumps(ret_val))


def get_topic_page(request, dataset, analysis, number):
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
    ret_val['topics'] = [vars(AjaxTopic(topic, get_topic_name(topic,
        name_scheme_id))) for topic in topics]
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


class AjaxTopic(object):
    def __init__(self, topic, topic_name):
        self.name = str(topic.number) + ": " + topic_name
        self.number = topic.number
        try:
            # TODO(matt): This looks like it gets the wrong name
            self.topicgroup = [topic.name for topic
                               in topic.topicgroup.subtopics]
        except:
            self.topicgroup = False

# Topic Groups

def create_topic_group(request, dataset, analysis, name):
    analysis = Analysis.objects.get(dataset__name=dataset, name=analysis)
    number = Topic.objects.aggregate(Min('number'))['number__min'] - 1#usually < 0...
    topic_group = TopicGroup(analysis=analysis, name=name, number=number)
    topic_group.total_count = 0
    topic_group.save()
    return HttpResponse('Group %d:"%s" Created!' % (topic_group.number, topic_group.name))

def remove_topic_group(request, number):
    number = int(number)
    topic_group = TopicGroup.objects.get(number=number)
    topic_group.delete()
    return HttpResponse('Group %d removed.' % number)

@transaction.commit_manually
def clear_topic_group(topic_group):
    topic_group.total_count = 0
    for topic_word in topic_group.topicword_set.all():
        topic_word.delete()
    for doctop in topic_group.documenttopic_set.all():
        doctop.delete()
    for avt in topic_group.attributevaluetopic_set.all():
        avt.delete()
    for doctopword in topic_group.documenttopicword_set.all():
        doctopword.delete()

    transaction.commit()

@transaction.commit_manually
def reaggregate_words(topic_group):
    words = {}
    for topic in topic_group.subtopics:
        for topic_word in topic.topicword_set.all():
            words[topic_word.word] = words.get(topic_word.word, 0) + topic_word.count
            topic_group.total_count += topic_word.count

    for word, count in words.iteritems():
        TopicWord(topic=topic_group, word=word, count=count).save()
    topic_group.save()

    transaction.commit()

@transaction.commit_manually
def reaggregate_docs(topic_group):
    docs = {}
    for topic in topic_group.subtopics:
        for dt in topic.documenttopic_set.all():
            docs[dt.document] = docs.get(dt.document, 0) + dt.count

    for doc, count in docs.iteritems():
        DocumentTopic(topic=topic_group, document=doc, count=count).save()

    transaction.commit()

@transaction.commit_manually
def reaggregate_attrs(topic_group):
    attrs = {}
    for topic in topic_group.subtopics:
        for avt in topic.attributevaluetopic_set.all():
            attrs[avt.value] = attrs.get(avt.value, 0) + avt.count

    for val, count in attrs.iteritems():
        AttributeValueTopic(topic=topic_group,
                            value=val,
                            attribute=val.attribute,
                            count=count).save()

    transaction.commit()

@transaction.commit_manually
def reaggregate_doctopicword(topic_group):
    doctopwords = {}
    for topic in topic_group.subtopics:
        for dtw in topic.documenttopicword_set.all():
            count = doctopwords.get((dtw.topic, dtw.word, dtw.document), 0)
            doctopwords[dtw.topic, dtw.word, dtw.document] = count + dtw.count

    for keys, count in doctopwords.iteritems():
        topic, word, doc = keys
        DocumentTopicWord(topic=topic,
                          word=word,
                          document=doc,
                          count=count).save()

    transaction.commit()

def reaggregate_topicgroup(topic_group):
    clear_topic_group(topic_group)
    reaggregate_words(topic_group)
    reaggregate_docs(topic_group)
    reaggregate_attrs(topic_group)
    reaggregate_doctopicword(topic_group)

def add_topic_to_group(request, dataset, analysis, number, addnumber):
    analysis = Analysis.objects.get(dataset__name=dataset, name=analysis)
    topic_group = analysis.topic_set.get(number=number).topicgroup
    topic = analysis.topic_set.get(number=addnumber)
    if topic not in topic_group.subtopics:
        TopicGroupTopic(topic=topic, group=topic_group).save()
        reaggregate_topicgroup(topic_group)
        return HttpResponse('Added topic %d to group %d' % (topic.number, topic_group.number))

def remove_topic_from_group(request, dataset, analysis, number, addnumber):
    analysis = Analysis.objects.get(dataset__name=dataset, name=analysis)
    topic_group = analysis.topic_set.get(number=number).topicgroup
    topic = analysis.topic_set.get(number=addnumber)
    if topic in topic_group.subtopics:
        TopicGroupTopic.objects.get(topic=topic, group=topic_group).delete()
        reaggregate_topicgroup(topic_group)
        return HttpResponse('Removed topic %d to group %d' % (topic.number, topic_group.number))

# vim: et sw=4 sts=4
