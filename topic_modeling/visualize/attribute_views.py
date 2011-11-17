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


from django.shortcuts import get_object_or_404

from topic_modeling.visualize.charts import get_chart
from topic_modeling.visualize.common.ui import BreadCrumb, Tab,\
    Widget, WordSummary
from topic_modeling.visualize.common.views import AnalysisBaseView
from topic_modeling.visualize.common.helpers import get_word_cloud, paginate_list, set_word_context
from topic_modeling.visualize.models import Attribute
from topic_modeling.visualize.models import Document
from topic_modeling.visualize.models import Value
from topic_modeling.visualize.models import Word

class AttributeView(AnalysisBaseView):
    template_name = "attributes.html"
    
    def get_context_data(self, request, **kwargs):
        context = super(AttributeView, self).get_context_data(request, **kwargs)
        
        dataset = context['dataset']
        analysis = context['analysis']
        attribute = kwargs['attribute'] if 'attribute' in kwargs else None
        try:
            value = kwargs['value']
        except KeyError:
            value = ''
        
        context['highlight'] = 'attributes_tab'
        context['tab'] = 'attribute'
        context['attributes'] = dataset.attribute_set.all()
        if attribute:
            attribute = get_object_or_404(Attribute, dataset=dataset,
                    name=attribute)
            prev_attribute = request.session.get('attribute-name', '')
            if prev_attribute != attribute.name:
                request.session['attribute-name'] = attribute.name
                request.session['attribute-page'] = 1
        else:
            request.session['attribute-page'] = 1
            attribute = context['attributes'][0]
    
        context['attribute'] = attribute
    
        values = attribute.value_set.all()
        page_num = request.session.get('attribute-page', 1)
        num_per_page = request.session.get('attributes-per-page', 20)
        values, num_pages, _ = paginate_list(values, page_num, num_per_page)
        context['num_pages'] = num_pages
        context['page_num'] = page_num
        context['values'] = [v.value for v in values]
    
        if value:
            value = get_object_or_404(Value, attribute=attribute, value=value)
        else:
            value = values[0]
        context['value'] = value
        
        context['view_description'] = "Attribute '{0}'".format(attribute.name)
        context['tabs'] = [attribute_info_tab(analysis, attribute, value, context['analysis_url'], context['attributes_url'])]
        context['breadcrumb'] = \
            BreadCrumb().item(dataset).item(analysis).item(attribute).item(value)
        
        return context


class AttributeWordView(AttributeView):
    template_name = "attribute_word.html"
    
    def get_context_data(self, request, **kwargs):
        context = super(AttributeWordView, self).get_context_data(request, **kwargs)
        dataset = context['dataset']
        analysis = context['analysis']
        attribute = context['attribute']
        value = context['value']
        word = Word.objects.get(dataset=dataset, type=kwargs['word'])
        documents = word.document_set.filter(attribute=attribute,
                attributevaluedocument__value=value)
        words = []
        for document in documents:
            w = WordSummary(word.type)
            set_word_context(w, document, analysis)
            words.append(w)
            w.url = '%s/%s/values/%s/documents/%d?kwic=%s' \
                % (context['attributes_url'], attribute.name, value.value,
                   document.id, word.type)
            w.doc_name = document.filename
            w.doc_id = document.id
    
        context['words'] = words
        context['breadcrumb'].word(word)
        context['attribute_post_link'] = '/words/%s' % word.type
    
        return context

class AttributeDocumentView(AttributeView):
    template_name = "attribute_document.html"
    
    def get_context_data(self, request, **kwargs):
        context = super(AttributeDocumentView, self).get_context_data(request, **kwargs)
        document = Document.objects.get(dataset=context['dataset'], id=kwargs['document'])
        if request.GET and request.GET['kwic']:
            context['text'] = document.text(request.GET['kwic'])
        else:
            context['text'] = document.text()
        context['breadcrumb'].document(document)
        return context


def attribute_info_tab(analysis, attribute, value, analysis_url, attributes_url):
    tab = Tab('Attribute Information', 'attributes/attribute_info')
    
    token_count = attribute.attributevalue_set.get(value=value).token_count
    words = get_words(attribute, value, attributes_url, token_count)
    
    tab.add(metrics_widget(attribute, value, token_count))
    tab.add(top_words_chart_widget(words))
    tab.add(word_cloud_widget(words))
    ngram_widget = ngram_word_cloud_widget(attribute, value, attributes_url, token_count)
    if ngram_widget: tab.add(ngram_widget)
    tab.add(topic_cloud_widget(analysis, attribute, value, analysis_url, token_count))
    
    return tab

def get_attrvalwords(attribute, value):
    attrvalwords = attribute.attributevalueword_set.filter(
            value=value).order_by('-count')
    attrvalwords = attrvalwords.filter(word__ngram=False)
    return attrvalwords

def get_words(attribute, value, attributes_url, token_count):
    words = []
    attrvalwords = get_attrvalwords(attribute, value)
    for attrvalword in attrvalwords[:100]:
        type = attrvalword.word.type
        percent = float(attrvalword.count) / token_count
        w = WordSummary(type, percent)
        w.url = (attributes_url+'/'+attribute.name+'/values/'+
                value.value+'/words/'+type)
        words.append(w)
    return words

def get_topics(analysis, attribute, value, analysis_url, token_count):
    topics = []
    topic_set = analysis.topic_set.all()
    attrvaltopics = attribute.attributevaluetopic_set.filter(value=value,
            topic__in=topic_set).order_by('-count')
    for attrvaltopic in attrvaltopics[:10]:
        type = attrvaltopic.topic.name
        percent = float(attrvaltopic.count) / token_count
        t = WordSummary(type, percent)
        t.url = analysis_url + '/topics/%s' % (attrvaltopic.topic.number)
        topics.append(t)
    return topics

def get_ngrams(attribute, value, attributes_url, tokens):
    attrvalngrams = attribute.attributevalueword_set.filter(
            value=value).order_by('-count')
    attrvalngrams = attrvalngrams.filter(word__ngram=True)
    ngrams = []
    for attrvalngram in attrvalngrams[:10]:
        type = attrvalngram.word.type
        percent = float(attrvalngram.count) / tokens
        w = WordSummary(type, percent)
        w.url = (attributes_url+'/'+attribute.name+'/values/'+
                value.value+'/words/'+type)
        ngrams.append(w)
    return ngrams

def metrics_widget(attribute, value, token_count):
    w = Widget('Metrics', 'attributes/metrics')
    attrvaldocs = attribute.attributevaluedocument_set.filter(value=value)
    attrvalwords = get_attrvalwords(attribute, value)
    w['num_tokens'] = token_count
    w['num_types'] = attrvalwords.count()
    w['num_docs'] = attrvaldocs.count()
    return w

def top_words_chart_widget(words):
    w = Widget('Top Words', 'attributes/top_words_chart')
    w['chart_address'] = get_chart(words)
    return w

def word_cloud_widget(words):
    w = Widget('Word Cloud', 'attributes/word_cloud')
    w['word_cloud'] = get_word_cloud(words)
    return w

def ngram_word_cloud_widget(attribute, value, attributes_url, token_count):
    ngrams = get_ngrams(attribute, value, attributes_url, token_count)
    if ngrams:
        w = Widget('N-gram Word Cloud', 'attributes/ngram_cloud')
        w['ngram_cloud'] = get_word_cloud(ngrams)
        return w
    else: return None

def topic_cloud_widget(analysis, attribute, value, analysis_url, token_count):
    w = Widget('Topic Cloud', 'attributes/topic_cloud')
    topics = get_topics(analysis, attribute, value, analysis_url, token_count)
    w['topic_cloud'] = get_word_cloud(topics, '[', ']')
    return w

# vim: et sw=4 sts=4
