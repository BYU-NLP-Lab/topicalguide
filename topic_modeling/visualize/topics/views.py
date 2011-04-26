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


import os
from collections import namedtuple

from django.db.models import Avg
from django.shortcuts import render_to_response, get_object_or_404
from django.template import Context
from django.http import HttpResponse
from django.http import HttpResponseNotFound

from topic_modeling.visualize.charts import get_chart
from topic_modeling.visualize.common import get_word_cloud, root_context
from topic_modeling.visualize.common import set_word_context
from topic_modeling.visualize.common import BreadCrumb
from topic_modeling.visualize.common import WordSummary
from topic_modeling.visualize.documents.views import add_top_topics
from topic_modeling.visualize.documents.views import add_similarity_measures as\
        doc_add_similarity_measures
from topic_modeling.visualize.models import Analysis
from topic_modeling.visualize.models import Dataset
from topic_modeling.visualize.models import Document
from topic_modeling.visualize.models import ExtraTopicInformation
from topic_modeling.visualize.models import Topic
from topic_modeling.visualize.models import Word
from topic_modeling.visualize.models import TopicName
from topic_modeling.visualize.models import TopicNameScheme
from topic_modeling.visualize.topics.common import RenameForm
from topic_modeling.visualize.topics.common import  get_topic_name
from topic_modeling.visualize.topics.common import SortTopicForm
from topic_modeling.visualize.topics.common import top_values_for_attr_topic
from topic_modeling.visualize.topics.filters import clean_topics_from_session
from topic_modeling.visualize.topics.filters import TopicFilterByDocument
from topic_modeling.visualize.topics.filters import TopicFilterByWord
from topic_modeling.visualize.word_views import add_word_charts
from topic_modeling.visualize.word_views import add_word_contexts

# The context variables that all topic views need
#################################################

def base_context(request, dataset, analysis, topic, extra_filters=[]):
    # Basic page variables here
    context = root_context(dataset, analysis)
    context['highlight'] = 'topics_tab'
    context['tab'] = 'topic'
    context['extra_widgets'] = []

    ds = Dataset.objects.get(name=dataset)
    context['topic_map_dir'] = ds.data_root + '/topic_maps'

    dataset = get_object_or_404(Dataset, name=dataset)
    analysis = get_object_or_404(Analysis, name=analysis, dataset=dataset)

    context['sort_form'] = SortTopicForm(analysis)

    sort_by = request.session.get('topic-sort', 'name')
    context['sort_form'].fields['sort'].initial = sort_by

    # Get the name scheme stuff ready
    name_schemes = TopicNameScheme.objects.filter(
            analysis=analysis).order_by('name')
    context['nameschemes'] = name_schemes
    if 'current_name_scheme_id' not in request.session:
        request.session['current_name_scheme_id'] = name_schemes[0].id

    current_name_scheme_id = request.session['current_name_scheme_id']
    current_name_scheme = TopicNameScheme.objects.get(id=current_name_scheme_id)
    context['currentnamescheme'] = current_name_scheme

    # Filter, sort, and paginate the topics
    if topic:
        topic = get_object_or_404(Topic, number=topic, analysis=analysis)
    topics = analysis.topic_set
    topics, filter_form, num_pages = clean_topics_from_session(topics,
            request.session, extra_filters, topic)
    page_num = request.session.get('topic-page', 1)
    context['topics'] = topics
    context['filter'] = filter_form
    context['num_pages'] = num_pages
    context['page_num'] = page_num
    if not topic:
        topic = context['topics'][0]
    context['curtopic'] = topic

    context['metrics'] = topic.topicmetricvalue_set.all()

    topic_name = get_topic_name(topic, current_name_scheme.id)

    context['topic_name'] = topic_name

    # Build the bread crumb
    context['breadcrumb'] = BreadCrumb()
    context['breadcrumb'].dataset(dataset)
    context['breadcrumb'].analysis(analysis)
    context['breadcrumb'].topic(topic.number, topic_name)

    return context, analysis, topic


# Top-level view methods
########################

def index(request, dataset, analysis, topic):
    context, analysis, topic = base_context(request, dataset, analysis, topic)

    top_level_widgets = []
    top_level_widgets.append(top_words_widgets(topic, context))
    top_level_widgets.append(similar_topics_widgets(request, analysis, topic,
            context))
    top_level_widgets.append(extra_information_widgets(request, analysis,
            topic, context))
    top_level_widgets[0].hidden = False
    add_turbo_topics(analysis, topic, context)
    context['top_level_widgets'] = top_level_widgets

    rename_form = RenameForm(context['topic_name'])
    context['rename_form'] = rename_form

    return render_to_response('topic.html', context)


def word_index(request, dataset, analysis, topic, word):
    dataset_name = dataset
    dataset = Dataset.objects.get(name=dataset_name)

    filter = TopicFilterByWord(Analysis.objects.get(dataset=dataset,
            name=analysis), 0)
    filter.current_word = word

    context, analysis, topic = base_context(request, dataset_name, analysis,
            topic, extra_filters=[filter])

    word = Word.objects.get(dataset=dataset, type=word)
    context['curword'] = word
    documents = word.documenttopicword_set.filter(topic=topic).order_by(
            'document__filename')
    docs = []
    for dtw in documents:
        d = dtw.document
        w = WordSummary(word.type)
        set_word_context(w, d, analysis, topic.number)
        docs.append(w)
        w.url = "%s/%d/documents/%d?kwic=%s" % (context['topics_url'],
                topic.number, d.id, word.type)
        w.doc_name = d.filename
        w.doc_id = d.id
    context['documents'] = docs
    context['breadcrumb'].word(word)
    context['topic_post_link'] = '/words/%s' % word.type

    add_word_charts(dataset, analysis, context)

    topicword = topic.topicword_set.get(word=word,word__ngram=False)
    word_url = '%s/%d/words/' % (context['topics_url'], topic.number)
    add_word_contexts(topicword.word.type, word_url, context)

    return render_to_response('topic_word.html', context)


def document_index(request, dataset, analysis, topic, document):
    filter = TopicFilterByDocument(Analysis.objects.get(dataset__name=dataset,
            name=analysis), 0)
    filter.current_document_id = document
    context, analysis, topic = base_context(request, dataset, analysis, topic,
            extra_filters=[filter])

    document = Document.objects.get(dataset__name=dataset, id=document)
    text = document.get_highlighted_text([topic.number], analysis)
    context['metrics'] = document.documentmetricvalue_set.all()

    add_top_topics(request, analysis, document, context)
    doc_add_similarity_measures(request, analysis, document, context)

    context['document_title'] = document.filename
    context['document_text'] = text
    context['breadcrumb'].document(document)
    context['topic_post_link'] = '/documents/%s' % document.id

    return render_to_response('topic_document.html', context)


# Not a top-level view, but it's a directly-responding method, so it goes
# roughly in this category
def topic_map(request, dataset, analysis, topic, namescheme):
    context, analysis, topic = base_context(request, dataset, analysis, topic)

    path = str(topic.analysis.name) + '/' + namescheme + '/' + \
            str(topic.number) + '.svg'
    topic_map_local = context['topic_map_dir'] + '/' + path

    if os.path.exists(topic_map_local):
        image = open(topic_map_local, 'r').read()
        return HttpResponse(image, mimetype="image/svg+xml")
    else:
        return HttpResponseNotFound()


# Topic index widgets
#####################

# Top level widgets create groups of lower-level widgets.  Each lower level
# widget must specify a url, a title, and whether or not it defaults to visible
# (only one widget per top level widget should default to visible).
#
# The code that produces widgets also needs to set context variables for
# whatever is needed by the url they specify.

# Top Words widgets
###################

def top_words_widgets(topic, context):
    top_level_widget = TopLevelWidget("Top Words")

    word_url = '%s/%d/words/' % (context['topics_url'], topic.number)
    topicwords = topic.topicword_set.filter(
            word__ngram=False).order_by('-count')
    words = []
    for topicword in topicwords[:100]:
        percent = float(topicword.count) / topic.total_count
        w = WordSummary(topicword.word.type, percent)
        w.url = word_url + topicword.word.type
        words.append(w)

    # TODO(matt): put other word clouds in here (ngrams, turbo topics)
    top_level_widget.widgets.append(word_cloud_widget(words, context))
    top_level_widget.widgets.append(words_in_context_widget(words, context))
    top_level_widget.widgets.append(word_chart_widget(words, context))
    top_level_widget.widgets[0].hidden = False
    return top_level_widget


def word_cloud_widget(words, context):
    word_cloud = Widget("Word Cloud", "topic_widgets/word_cloud.html")
    context['word_cloud'] = get_word_cloud(words)
    return word_cloud


def words_in_context_widget(words, context):
    words_in_context = Widget("Words in Context",
            "topic_widgets/words_in_context.html")
    context['words_in_context'] = words[:10]
    return words_in_context


def word_chart_widget(words, context):
    word_chart = Widget("Word Chart", "topic_widgets/word_chart.html")
    context['chart_address'] = get_chart(words)
    return word_chart


def add_ngrams(topic, context):
    word_url = '%s/%d/words/' % (context['topics_url'], topic.number)
    topicngrams = topic.topicword_set.filter(
            word__ngram=True).order_by('-count')
    ngrams = []
    for topicngram in topicngrams[:10]:
        percent = float(topicngram.count) / topic.total_count
        w = WordSummary(topicngram.word.type, percent)
        w.url = word_url + topicngram.word.type
        ngrams.append(w)
    if ngrams:
        context['ngram_cloud'] = get_word_cloud(ngrams)


def add_turbo_topics(analysis, topic, context):
    try:
        turbo_topics = analysis.extratopicinformation_set.get(
                name="Turbo Topics Cloud")
        value = turbo_topics.extratopicinformationvalue_set.get(topic=topic)
        text = value.value
        words = []
        total = 0
        for line in text.split('\n')[:100]:
            if line.isspace() or not line:
                continue
            fields = line.split()
            type = '_'.join(fields[:-1])
            count = float(fields[-1])
            words.append((type, count))
            total += count
        summaries = []
        for type, count in words:
            w = WordSummary(type, count / total)
            summaries.append(w)
        context['turbo_topics_cloud'] = get_word_cloud(summaries, url=False)
        context['extra_widgets'].append('topic_widgets/turbo_topics_cloud.html')
    except ExtraTopicInformation.DoesNotExist:
        pass
    try:
        turbo_topics = analysis.extratopicinformation_set.get(
                name="Turbo Topics N-Grams")
        value = turbo_topics.extratopicinformationvalue_set.get(topic=topic)
        text = value.value
        first_ten = text.split('\n')[:10]
        rest = text.split('\n')[10:]
        context['turbo_topics_less'] = '\n'.join(first_ten)
        context['turbo_topics_more'] = '\n'.join(rest)
        context['extra_widgets'].append('topic_widgets/turbo_topics.html')
    except ExtraTopicInformation.DoesNotExist:
        pass


# Similar Topics Widgets
########################

def similar_topics_widgets(request, analysis, topic, context):
    top_level_widget = TopLevelWidget("Similar Topics")

    top_level_widget.widgets.append(similar_topic_list_widget(request,
        analysis, topic, context))
    top_level_widget.widgets.append(topic_map_widget(topic, context))
    top_level_widget.widgets[0].hidden = False
    return top_level_widget


def similar_topic_list_widget(request, analysis, topic, context):
    topic_list = Widget("Lists", "topic_widgets/similar_topics.html")
    similarity_measures = analysis.pairwisetopicmetric_set.all()
    if similarity_measures:
        name_scheme_id = request.session['current_name_scheme_id']
        ns = TopicNameScheme.objects.get(id=name_scheme_id)
        measure = request.session.get('topic-similarity-measure', None)
        if measure:
            measure = similarity_measures.get(name=measure)
        else:
            measure = similarity_measures[0]

        similar_topics = topic.pairwisetopicmetricvalue_originating.\
                select_related().filter(metric=measure).order_by('-value')
        entries = []
        for t in similar_topics[1:11]:
            topic = t.topic2
            number = topic.number
            name = str(number) + ': ' + get_topic_name(topic, name_scheme_id)
            entries.append(TopicSimilarityEntry(name, number, t.value))
        context['similar_topics'] = entries
        context['similarity_measures'] = similarity_measures
        context['similarity_measure'] = measure
    return topic_list


def topic_map_widget(topic, context):
    topic_map = Widget("Map", "topic_widgets/topic_map.html")
    path = str(topic.analysis.name) + '/' + context['currentnamescheme'].name \
            + '/' + str(topic.number) + '.svg'
    topic_map_local = context['topic_map_dir'] + '/' + path
    if os.path.exists(topic_map_local):
        context['topic_map_local_filename'] = topic_map_local
        topic_map_url = '/datasets/' + str(topic.analysis.dataset.name) + \
                '/analyses/' + str(topic.analysis.name) + '/topics/' + \
                str(topic.number) + '/maps/' + \
                context['currentnamescheme'].name
        context['topic_map_url'] = topic_map_url
    return topic_map


# Extra Information Widgets
###########################

def extra_information_widgets(request, analysis, topic, context):
    top_level_widget = TopLevelWidget("Extra Information")

    top_level_widget.widgets.append(stats_widget(topic, context))
    top_level_widget.widgets.append(top_documents_widget(topic, context))
    top_level_widget.widgets.append(top_values_widget(request, analysis, topic,
            context))
    print top_level_widget.widgets
    top_level_widget.widgets[0].hidden = False
    return top_level_widget


def stats_widget(topic, context):
    stats = Widget('Stats', 'topic_widgets/stats.html')
    Metric = namedtuple('Metric', 'name value average')
    metrics = []
    for topicmetricvalue in topic.topicmetricvalue_set.select_related().all():
        metric = topicmetricvalue.metric
        name = metric.name
        value = topicmetricvalue.value
        average = metric.topicmetricvalue_set.aggregate(Avg('value'))
        metrics.append(Metric(name, value, average['value__avg']))
    context['metrics'] = metrics
    return stats


def top_documents_widget(topic, context):
    top_documents = Widget('Top Documents', 'topic_widgets/top_documents.html')
    topicdocs = topic.documenttopic_set.order_by('-count')[:10]
    context['top_docs'] = topicdocs
    return top_documents


def top_values_widget(request, analysis, topic, context):
    top_values_widget = Widget('Top Values', 'topic_widgets/top_values.html')
    context['attributes'] = analysis.dataset.attribute_set.all()
    current_attribute = request.session.get('topic-attribute', None)
    if not current_attribute:
        if len(context['attributes'])==0: return
        attribute = context['attributes'][0]
    else:
        attribute = analysis.dataset.attribute_set.get(name=current_attribute)
    top_values = top_values_for_attr_topic(analysis, topic, attribute)

    context['attribute'] = attribute
    context['top_values'] = top_values
    return top_values_widget


# Classes
#########

class TopLevelWidget(object):
    def __init__(self, title):
        self.title = title
        self.ref = title.lower().replace(' ', '-')
        self.widgets = []
        self.hidden = True


class Widget(object):
    def __init__(self, title, url):
        self.title = title
        self.url = url
        self.hidden = True


class TopicSimilarityEntry(object):
    def __init__(self, name, number, value):
        self.name = name
        self.number = number
        self.value = value


# vim: et sw=4 sts=4
