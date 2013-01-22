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

from django.http import HttpResponse
from django.db.models.aggregates import Min

from topic_modeling.visualize.common.ui import FilterForm
from topic_modeling.visualize.common.helpers import paginate_list
from topic_modeling.visualize.models import Analysis#, DocumentTopicWord
#from topic_modeling.visualize.models import Attribute
from topic_modeling.visualize.models import Topic
from topic_modeling.visualize.models import TopicGroup
from topic_modeling.visualize.models import TopicGroupTopic
#from topic_modeling.visualize.models import TopicWord
#from topic_modeling.visualize.models import DocumentTopic
#from topic_modeling.visualize.models import AttributeValueTopic
from topic_modeling.visualize.topics.common import top_values_for_attr_topic
from topic_modeling.visualize.topics.filters import clean_topics_from_session
from topic_modeling.visualize.topics.filters import get_topic_filter_by_name
from topic_modeling.visualize.topics.filters import possible_topic_filters
# from django.db import transaction
from topic_modeling.visualize.topics.names import current_name_scheme,\
    topic_name_with_ns
from django.views.decorators.http import require_GET
from topic_modeling.visualize.common.http_responses import JsonResponse
from topic_modeling.visualize import sess_key
from django.db.models import Avg, Min, Max

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
    analysis = Analysis.objects.get(dataset__name=dataset, name=analysis)
    
    request.session[sess_key(dataset,'topic-sort')] = order_by
    request.session[sess_key(dataset,'topic-page')] = 1
    ns = current_name_scheme(request.session, analysis)
    ret_val = dict()
    topics = analysis.topics
    topics, _, num_pages = clean_topics_from_session(dataset, topics, request.session)
    ret_val['topics'] = [vars(AjaxTopic(topic, topic_name_with_ns(topic, ns))) for topic in topics]
    ret_val['num_pages'] = num_pages
    ret_val['page'] = 1
    return JsonResponse(ret_val)


@require_GET
def topic_page(request, dataset, analysis, number):
    analysis = Analysis.objects.get(name=analysis, dataset__name=dataset)
    request.session[sess_key(dataset,'topic-page')] = int(number)
    ns = current_name_scheme(request.session, analysis)
    ret_val = dict()
    topics = request.session.get(sess_key(dataset,'topics-list'), None)
    if not topics:
        topics = analysis.topics()
#        topics = Topic.objects.filter(analysis__name=analysis,
#                analysis__dataset__name=dataset)
    num_per_page = request.session.get('topics-per-page', 20)
    page = int(number)
    topics, num_pages, page = paginate_list(topics, page, num_per_page)
    ret_val['topics'] = [vars(AjaxTopic(topic, topic_name_with_ns(topic, ns))) for topic in topics]
    ret_val['num_pages'] = num_pages
    ret_val['page'] = page
    return JsonResponse(ret_val)


# Widgets
#########

def top_attrvaltopic(request, dataset, analysis, topic, attribute, order_by):
    ret_val = dict()
    request.session[sess_key(dataset,'topic-attribute')] = attribute
    attribute = Attribute.objects.get(dataset__name=dataset, name=attribute)
    analysis = Analysis.objects.get(dataset__name=dataset, name=analysis)
    topic = analysis.topics.get(number=topic)
    top_values = top_values_for_attr_topic(topic=topic, attribute=attribute, order_by=order_by)
    ret_val['attribute'] = attribute.name
    ret_val['values'] = [vars(v) for v in top_values]
    return JsonResponse(ret_val)

def similar_for_topic(analysis, topic, metric, max=10):
    return topic.pairwisetopicmetricvalue_originating.\
            select_related().filter(metric=metric).order_by('-value')[1:1 + max]

def get_topic_info(topic):
    info = {
        'names': [item.name for item in topic.names.all()],
        'metrics': dict((m.metric.name, m.value) for m in topic.topicmetricvalues.all()),
        'documents': list(topic.topic_document_counts(sort=True)[:10])
    }
    return info

def get_metrics(analysis):
    res = {}
    for metric in analysis.topicmetrics.all():
        data = metric.values.aggregate(Avg('value'), Min('value'), Max('value'))
        res[metric.name] = {
            'min': data['value__min'],
            'max': data['value__max'],
            'avg': data['value__avg']
        }
    return res

def all_similar_topics(request, dataset, analysis, measure):
    '''An ajax view for listing a matrix of pairwise topic correlation
    
    @url /feeds/similar-topics/@dataset/@analysis/@measure$
    @name all-similar-topics

    measure = name of a pairwise topic matric
    dataset = name of a dataset
    analysis = name of an analysis for the dataset

    Returns:
        {
            'matrix': m x m matrix (m = number of topics in the analysis)
                      where matrix[i][j] = correlation between topic i and topic j,
            'topics': [{
                'names': list of topic names,
                'metrics': dict of metric values,
                'documents': list of top 10 documents,
                'topics': list of top 10 correlated topics
            }, ... for each topic (where index = topic.number)],
            'metrics': get_metrics(analysis)
        }
    '''
    analysis = Analysis.objects.get(dataset__name=dataset, name=analysis)
    ns = current_name_scheme(request.session, analysis)
    ret_val = dict()
    topics = list(analysis.topics.all().order_by('number'))
    measure = analysis.pairwisetopicmetrics.get(name__iexact=measure)

    matrix = [[0 for x in range(len(topics))] for x in range(len(topics))]
    info = []
    metrics = get_metrics(analysis)

    for topic in topics:
        tinfo = get_topic_info(topic)
        tinfo['topics'] = []
        for value in similar_for_topic(analysis, topic, measure):
            matrix[topic.number][value.topic2.number] = value.value
            tinfo['topics'].append(value.topic2.number)
        info.append(tinfo)

    return JsonResponse({'matrix': matrix, 'topics': info, 'metrics': metrics})

def similar_topics(request, dataset, analysis, topic, measure):
    '''And ajax view for listing topics similar to a given topic.

    measure = name of a measure
    topic   = (int) topic number
    analysis= name of an analysis
    dataset = name of a dataset

    returns (json):
    {
        'values': [float, ...] # the correlation values
        'topics': [info, ...]  # dicts of info about each topic
    }
    '''

    analysis = Analysis.objects.get(dataset__name=dataset, name=analysis)
    ns = current_name_scheme(request.session, analysis)
    ret_val = dict()
    request.session[sess_key(dataset,'topic-similarity-measure')] = measure
    topic = analysis.topics.get(number=topic)
    measure = analysis.pairwisetopicmetrics.get(name=measure)
    similar_topics = topic.pairwisetopicmetricvalue_originating.\
            select_related().filter(metric=measure).order_by('-value')[1:11]
    
    topics = []
    values = []
    for t in similar_topics:
        values += [t.value]
        similar_topic = t.topic2
        topic_name = topic_name_with_ns(similar_topic, ns)
        topics += [vars(AjaxTopic(similar_topic, topic_name))]
    ret_val['values'] = values
    ret_val['topics'] = topics
    return JsonResponse(ret_val)


# Filters
#########

def new_topic_filter(request, dataset, analysis, topic, name):
    analysis = Analysis.objects.get(dataset__name=dataset, name=analysis)
    filters = request.session.get(sess_key(dataset,'topic-filters'), [])
    filter_form = FilterForm(possible_topic_filters(analysis))
    id = 0
    for filter in filters:
        filter.id = id
        filter_form.add_filter(filter)
        id += 1
    ## ISSUE 2.1 this is breaking on no Dataset.attribute_set
    new_filter = get_topic_filter_by_name(name)(analysis, id)
    filter_form.add_filter(new_filter)
    filters.append(new_filter)
    request.session[sess_key(dataset,'topic-filters')] = filters
    return HttpResponse(filter_form.__unicode__())


def remove_topic_filter(request, dataset, analysis, topic, number):
    request.session[sess_key(dataset,'topic-filters')].pop(int(number))
    request.session.modified = True
    return filtered_topics_response(request, dataset, analysis)


def filtered_topics_response(request, dataset, analysis):
    analysis = Analysis.objects.get(dataset__name=dataset, name=analysis)
    ns = current_name_scheme(request.session, analysis)
    topics = analysis.topics
    request.session[sess_key(dataset,'topic-page')] = 1
    topics, filter_form, num_pages = clean_topics_from_session(dataset, topics, request.session)
    ret_val = dict()
    ret_val['filter_form'] = filter_form.__unicode__()
    ret_val['topics'] = [vars(AjaxTopic(topic, topic_name_with_ns(topic, ns))) for topic in topics]
    ret_val['num_pages'] = num_pages
    ret_val['page'] = request.session.get(sess_key(dataset,'topic-page'), 1)
    return JsonResponse(ret_val)


def update_topic_attribute_filter(request, dataset, analysis, topic, number,
        attribute, value=None):
    filter = request.session[sess_key(dataset,'topic-filters')][int(number)]
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
    filter = request.session[sess_key(dataset,'topic-filters')][int(number)]
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
    filter = request.session[sess_key(dataset,'topic-filters')][int(number)]
    if document == 'None':
        filter.current_document_id = None
    else:
        filter.current_document_id = document
    filter.remake_form()
    request.session.modified = True
    return filtered_topics_response(request, dataset, analysis)


def update_topic_word_filter(request, dataset, analysis, topic, number, word):
    filter = request.session[sess_key(dataset,'topic-filters')][int(number)]
    if word == 'None':
        filter.current_word = None
    else:
        filter.current_word = word
    filter.remake_form()
    request.session.modified = True
    return filtered_topics_response(request, dataset, analysis)


class AjaxTopic(object):
    def __init__(self, topic, topic_name):
        self.name = topic_name
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

# @transaction.commit_manually
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

    # transaction.commit()

# @transaction.commit_manually
def reaggregate_words(topic_group):
    words = {}
    for topic in topic_group.subtopics:
        for topic_word in topic.topicword_set.all():
            words[topic_word.word] = words.get(topic_word.word, 0) + topic_word.count
            topic_group.total_count += topic_word.count

    for word, count in words.iteritems():
        TopicWord(topic=topic_group, word=word, count=count).save()
    topic_group.save()

    # transaction.commit()

# @transaction.commit_manually
def reaggregate_docs(topic_group):
    docs = {}
    for topic in topic_group.subtopics:
        for dt in topic.documenttopic_set.all():
            docs[dt.document] = docs.get(dt.document, 0) + dt.count

    for doc, count in docs.iteritems():
        DocumentTopic(topic=topic_group, document=doc, count=count).save()

    # transaction.commit()

# @transaction.commit_manually
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

    # transaction.commit()

# @transaction.commit_manually
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

    # transaction.commit()

def reaggregate_topicgroup(topic_group):
    clear_topic_group(topic_group)
    reaggregate_words(topic_group)
    reaggregate_docs(topic_group)
    reaggregate_attrs(topic_group)
    reaggregate_doctopicword(topic_group)

def add_topic_to_group(request, dataset, analysis, number, addnumber):
    analysis = Analysis.objects.get(dataset__name=dataset, name=analysis)
    topic_group = analysis.topics.get(number=number).topicgroup
    topic = analysis.topics.get(number=addnumber)
    if topic not in topic_group.subtopics:
        TopicGroupTopic(topic=topic, group=topic_group).save()
        reaggregate_topicgroup(topic_group)
        return HttpResponse('Added topic %d to group %d' % (topic.number, topic_group.number))

def remove_topic_from_group(request, dataset, analysis, number, addnumber):
    analysis = Analysis.objects.get(dataset__name=dataset, name=analysis)
    topic_group = analysis.topics.get(number=number).topicgroup
    topic = analysis.topics.get(number=addnumber)
    if topic in topic_group.subtopics:
        TopicGroupTopic.objects.get(topic=topic, group=topic_group).delete()
        reaggregate_topicgroup(topic_group)
        return HttpResponse('Removed topic %d to group %d' % (topic.number, topic_group.number))

# vim: et sw=4 sts=4
