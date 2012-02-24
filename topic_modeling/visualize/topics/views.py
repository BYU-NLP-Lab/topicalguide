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

import os
from collections import namedtuple

from django.db.models import Avg
from django.http import HttpResponse, HttpResponseNotFound
from django.shortcuts import get_object_or_404

from topic_modeling.visualize.charts import get_chart
from topic_modeling.visualize.common.ui import BreadCrumb, Widget, WordSummary, Tab
from topic_modeling.visualize.common.views import AnalysisBaseView
from topic_modeling.visualize.common.helpers import word_cloud_widget, set_word_context, get_word_cloud, \
                                                    get_dataset_and_analysis
from topic_modeling.visualize.documents.views import tabs as doc_tabs
from topic_modeling.visualize.models import Analysis, Document, Topic, TopicMetaInfo, TopicMetaInfoValue, Word
from topic_modeling.visualize.topics import topic_attribute
from topic_modeling.visualize.topics.common import RenameForm, SortTopicForm, top_values_for_attr_topic
from topic_modeling.visualize.topics.filters import TopicFilterByDocument, TopicFilterByWord, clean_topics_from_session
from topic_modeling.visualize.topics.names import name_schemes, current_name_scheme, topic_name_with_ns
from topic_modeling.visualize.word_views import words_tab


class TopicView(AnalysisBaseView):
    template_name = "topics.html"
    
    def get_context_data(self, request, **kwargs):
        context = super(TopicView, self).get_context_data(request, **kwargs)
        
        if 'topic_filters' in kwargs:
            request.session['topic-filters'] = kwargs['topic_filters']
        
        dataset = context['dataset']
        analysis = context['analysis']
        topic = kwargs.get('topic', None)
        extra_filters = kwargs.get('extra_filters', [])
        
        
        #TODO: clean up this context by moving widget-specific entries into widget contexts
        
        
        context['highlight'] = 'topics_tab'
        context['tab'] = 'topic'
        context['extra_widgets'] = []
    
        context['sort_form'] = SortTopicForm(analysis)
    
        sort_by = request.session.get('topic-sort', 'name')
        context['sort_form'].fields['sort'].initial = sort_by
    
    
        context['nameschemes'] = name_schemes(analysis)
        context['currentnamescheme'] = current_name_scheme(request.session, analysis)
    
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
        context['topic'] = topic
        
        context['topic_url'] = context['topics_url'] + '/' + str(topic.number)
    
        context['metrics'] = topic.topicmetricvalue_set.all()
    
        topic_name = topic_name_with_ns(topic, context['currentnamescheme'])
    
        context['topic_name'] = topic_name
    
        # Build the bread crumb
        context['breadcrumb'] = BreadCrumb().item(dataset).item(analysis).topic(topic.number, topic_name)
        context['view_description'] = 'Topic "'+topic_name + '"'
        
        context['tabs'] = tabs(request, topic, context['topic_url'], \
                               context['IMAGES'], context['currentnamescheme'].name)
        
        return context

class TopicWordView(TopicView):
    template_name = 'topics.html'
    def get_context_data(self, request, **kwargs):
        dataset_name = kwargs['dataset']
        analysis_name = kwargs['analysis']
        word = Word.objects.get(dataset__name=dataset_name, type=kwargs['word'])
        
        filter = TopicFilterByWord(Analysis.objects.get(dataset__name=dataset_name,
                name=analysis_name), 0)
        filter.current_word = word
        
        context = super(TopicWordView, self).get_context_data(request, extra_filters=[filter], **kwargs)
        analysis = context['analysis']
        topic = context['topic']
        context['word'] = word
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
        
        word_url = '%s/%d/words/' % (context['topics_url'], topic.number)
        context['tabs'] = [self._topic_word_tab(analysis, word, word_url, context['IMAGES'])]
        
        return context
    
    def _topic_word_tab(self, analysis, word, word_url, images_url):
        tab = words_tab(analysis, word, word_url, images_url)
        tab.title = "Topic Word"
        return tab
    
    def _total_count_widget(self, word):
        w = Widget('Total Count', 'words/total_count')
        w['word_count'] = word.count
        return w
    
    def _word_in_context_widget(self, word):
        w = Widget('Word In Context', 'words/word_in_context')
        w['word'] = word
        return w
    
    def _top_topics_widget(self):
        pass
    
    def _top_documents_widget(self):
        pass

class TopicDocumentView(TopicView):
    template_name = 'topics.html'
    
    def get_context_data(self, request, **kwargs):
        dataset_name = kwargs['dataset']
        analysis_name = kwargs['analysis']
        document_id = kwargs['document']
        filter = TopicFilterByDocument(Analysis.objects.get(dataset__name=dataset_name,
                name=analysis_name), 0)
        filter.current_document_id = kwargs['document']
        context = super(TopicDocumentView, self).get_context_data(request, extra_filters=[filter], **kwargs)
        
        dataset = context['dataset']
        analysis = context['analysis']
        topic = context['topic']
        
        document = Document.objects.get(dataset=dataset, id=document_id)
        context['document'] = document
        text = document.get_highlighted_text([topic.number], analysis)
        context['metrics'] = document.documentmetricvalue_set.all()
        context['document_title'] = document.filename
        context['document_text'] = text
        context['breadcrumb'].document(document)
        context['topic_post_link'] = '/documents/%s' % document.id
    
        context['tabs'] = doc_tabs(request, analysis, document)
        
        return context


# Topic index widgets
#####################

# Top level widgets create groups of lower-level widgets.  Each lower level
# widget must specify a url, a title, and whether or not it defaults to visible
# (only one widget per top level widget should default to visible).
#
# The code that produces widgets also needs to set context variables for
# whatever is needed by the url they specify.

def tabs(request, topic, topic_url, images_url, name_scheme_name):
    tabs = []
    tabs.append(top_words_tab(topic, topic_url, images_url))
    tabs.append(similar_topics_tab(request, topic, name_scheme_name))
    tabs.append(extra_information_tab(request, topic, topic_url))
    return tabs

#NOTE: this is not currently being used
def topic_name_widget(topic_name):
    w = Widget('Topic Name', 'topics/topic_name')
    w['rename_form'] = RenameForm(topic_name)
    return w

# Top Words widgets
###################

def top_words_tab(topic, topic_url, images_url):
    tab = Tab("Top Words", path='topics/top_words')
    
    word_url = '%s/words/' % topic_url
    topicwords = topic.topicword_set.filter(
            word__ngram=False).order_by('-count')
    words = []
    for topicword in topicwords[:100]:
        percent = float(topicword.count) / topic.total_count
        w = WordSummary(topicword.word.type, percent)
        w.url = word_url + topicword.word.type
        words.append(w)
    
    tab.add(word_chart_widget(words))
    
#    tab.add(Widget('Word Cloud',content_html=unigram_cloud(words)))
    tab.add(word_cloud_widget(words, title='Word Cloud'))
    
    ttcloud = turbo_topics_cloud_widget(topic)
    if ttcloud: tab.add(ttcloud)
    
    ngcloud = ngram_cloud_widget(topic, word_url)
    if ngcloud: tab.add(ngcloud)
    
    tab.add(words_in_context_widget(images_url, words))
    
    return tab

def words_in_context_widget(images_url, words):
    w = Widget("Words in Context", "topics/words_in_context")
    w['IMAGES'] = images_url
    w['words'] = words[:5]
    return w

def word_chart_widget(words):
    w = Widget("Word Chart", 'topics/word_chart')
    w['chart_address'] = get_chart(words)
    return w

def unigram_cloud(words):
    return get_word_cloud(words)

def ngram_cloud_widget(topic, word_url):
    topicngrams = topic.topicword_set.filter(
            word__ngram=True).order_by('-count')
    ngrams = []
    for topicngram in topicngrams[:10]:
        percent = float(topicngram.count) / topic.total_count
        w = WordSummary(topicngram.word.type, percent)
        w.url = word_url + topicngram.word.type
        ngrams.append(w)
    if ngrams:
        # Name must not contain spaces!
        return word_cloud_widget(ngrams, title='N-grams')
    return None


def turbo_topics_cloud_widget(topic):
    try:
        turbo_topics = TopicMetaInfo.objects.get(name="Turbo Topics Cloud")
        value = turbo_topics.topicmetainfovalue_set.get(topic=topic)
#        turbo_topics = analysis.extratopicinformation_set.get(
#                name="Turbo Topics Cloud")
#        value = turbo_topics.extratopicinformationvalue_set.get(topic=topic)
        text = value.value()
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
        # Name must not contain spaces!
        return word_cloud_widget(summaries, url=False)
    except (TopicMetaInfo.DoesNotExist,
            TopicMetaInfoValue.DoesNotExist):
        pass
    try:
        turbo_topics = TopicMetaInfo.objects.get(name="Turbo Topics N-Grams")
        value = turbo_topics.topicmetainfovalue_set.get(topic=topic)
        text = value.value
        first_ten = text.split('\n')[:10]
        rest = text.split('\n')[10:]
        # TODO(matt): make this into a cloud, called "Turbo Topics N-grams"
        # if we want to keep it.  Otherwise, just get rid of the second try
        # block.
        #context['turbo_topics_less'] = '\n'.join(first_ten)
        #context['turbo_topics_more'] = '\n'.join(rest)
        #context['extra_widgets'].append('widgets/topics/turbo_topics.html')
    except (TopicMetaInfo.DoesNotExist,
            TopicMetaInfoValue.DoesNotExist):
        pass
    return None


# Similar Topics Widgets
########################

def similar_topics_tab(request, topic, name_scheme_name):
    tab = Tab("Similar Topics", 'topics/similar_topics')
    tab.add(similar_topic_list_widget(request, topic))
    tab.add(topic_map_widget(topic, name_scheme_name))
    return tab


def similar_topic_list_widget(request, topic):
    w = Widget("Most Similar Topics", "topics/similar_topics")
    similarity_measures = topic.analysis.pairwisetopicmetric_set.all()
    if similarity_measures:
        ns = current_name_scheme(request.session, topic.analysis)
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
            name = str(number) + ': ' + topic_name_with_ns(topic, ns)
            entries.append(TopicSimilarityEntry(name, number, t.value))
        w['similar_topics'] = entries
        w['similarity_measures'] = similarity_measures
        w['similarity_measure'] = measure
    
    return w

#def topic_map_widget(topic, name_scheme_name):
#    analysis = topic.analysis
#    dataset = analysis.dataset
#    path = '%s/%s/%s/%s.svg' % (topic_map_dir(dataset), analysis.name, name_scheme_name, topic.number)
#    
#    w = Widget("Map", "topics/topic_map")
#    w['topic_map'] = open(path).read()
#    return w

def topic_map_dir(dataset):
    return dataset.dataset_dir + '/topic_maps'

def render_topic_map(request, dataset, analysis, topic, namescheme):
    dataset, analysis = get_dataset_and_analysis(dataset, analysis)
    path = '%s/%s/%s/%s.svg' % (topic_map_dir(dataset), analysis.name, namescheme, topic)
    if os.path.exists(path):
        image = open(path, 'r').read()
        return HttpResponse(image, mimetype="image/svg+xml")
    else:
        return HttpResponseNotFound()

def topic_map_widget(topic, name_scheme_name):
    analysis = topic.analysis
    dataset = analysis.dataset
    w = Widget("Map", "topics/topic_map")
    w['topic_map_url'] = '/datasets/%s/analyses/%s/topics/%d/maps/%s' \
        % (dataset.name, analysis.name, topic.number, name_scheme_name)
    return w


# Extra Information Widgets
###########################

def extra_information_tab(request, topic, topic_url):
    tab = Tab("Extra Information", 'topics/extra_information')
    tab.add(metrics_widget(topic))
    tab.add(metadata_widget(topic))
    tab.add(top_documents_widget(topic, topic_url))
    tab.add(top_values_widget(request, topic))
    return tab

def metrics_widget(topic):
    w = Widget('Metrics', 'topics/metrics')
    Metric = namedtuple('Metric', 'name value average')
    metrics = []
    for topicmetricvalue in topic.topicmetricvalue_set.select_related().all():
        metric = topicmetricvalue.metric
        name = metric.name
        value = topicmetricvalue.value
        average = metric.topicmetricvalue_set.aggregate(Avg('value'))
        metrics.append(Metric(name, value, average['value__avg']))
    w['metrics'] = metrics
    return w

def metadata_widget(topic):
    w = Widget('Metadata', 'common/metadata')
    w['metadataval_mgr'] = topic.topicmetainfovalue_set
    return w

def top_documents_widget(topic, topic_url):
    w = Widget('Top Documents', 'topics/top_documents')
    topicdocs = topic.documenttopic_set.order_by('-count')[:10]
    w['top_docs'] = topicdocs
    w['topic_url'] = topic_url
    return w

class NoValidCurrentAttribute(Exception): pass

def top_values_widget(request, topic):
    w = Widget('Top Values', 'topics/top_values')
    
    attribute = topic_attribute(topic.analysis.dataset, request.session)
    
    attributes = topic.analysis.dataset.attribute_set.all()
    current_attribute = request.session.get('topic-attribute', None)
    
    try:
        if current_attribute is None: raise NoValidCurrentAttribute
        try:
            attribute = topic.analysis.dataset.attribute_set.get(name=current_attribute)
        except Attribute.DoesNotExist:
            raise NoValidCurrentAttribute
    except NoValidCurrentAttribute:
        if len(attributes)==0: return
        attribute = attributes[0]
 
    top_values = top_values_for_attr_topic(topic, attribute)
    
    w['attributes'] = attributes
    w['attribute'] = attribute
    w['top_values'] = top_values
    return w


# Classes
#########

class TopicSimilarityEntry(object):
    def __init__(self, name, number, value):
        self.name = name
        self.number = number
        self.value = value


# vim: et sw=4 sts=4
