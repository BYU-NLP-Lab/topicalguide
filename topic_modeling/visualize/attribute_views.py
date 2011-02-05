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


from django.shortcuts import render_to_response, get_object_or_404

from topic_modeling.visualize.charts import get_chart
from topic_modeling.visualize.common import BreadCrumb
from topic_modeling.visualize.common import get_word_cloud
from topic_modeling.visualize.common import paginate_list
from topic_modeling.visualize.common import set_word_context
from topic_modeling.visualize.common import WordSummary
from topic_modeling.visualize.models import Analysis
from topic_modeling.visualize.models import Attribute
from topic_modeling.visualize.models import Dataset
from topic_modeling.visualize.models import Document
from topic_modeling.visualize.models import Value
from topic_modeling.visualize.models import Word

def base_page_vars(request, dataset, analysis, attribute, value):
    page_vars = dict()
    page_vars['highlight'] = 'attributes_tab'
    page_vars['tab'] = 'attribute'
    page_vars['dataset'] = dataset
    page_vars['analysis'] = analysis
    page_vars['baseurl'] = '/datasets/%s/analyses/%s/attributes' % (dataset,
            analysis)

    dataset = Dataset.objects.get(name=dataset)
    analysis = Analysis.objects.get(name=analysis, dataset=dataset)
    page_vars['attributes'] = dataset.attribute_set.all()
    if attribute:
        attribute = get_object_or_404(Attribute, dataset=dataset,
                name=attribute)
        prev_attribute = request.session.get('attribute-name', '')
        if prev_attribute != attribute.name:
            request.session['attribute-name'] = attribute.name
            request.session['attribute-page'] = 1
    else:
        request.session['attribute-page'] = 1
        attribute = page_vars['attributes'][0]

    page_vars['attribute'] = attribute

    values = attribute.value_set.all()
    page_num = request.session.get('attribute-page', 1)
    num_per_page = request.session.get('attributes-per-page', 20)
    values, num_pages, _ = paginate_list(values, page_num, num_per_page)
    page_vars['num_pages'] = num_pages
    page_vars['page_num'] = page_num
    page_vars['values'] = [v.value for v in values]

    if value:
        print attribute, value
        curvalue = get_object_or_404(Value, attribute=attribute, value=value)
    else:
        curvalue = values[0]

    page_vars['breadcrumb'] = BreadCrumb()
    page_vars['breadcrumb'].dataset(dataset)
    page_vars['breadcrumb'].analysis(analysis)
    page_vars['breadcrumb'].attribute(attribute)
    page_vars['breadcrumb'].value(curvalue)
    
    page_vars['curvalue'] = curvalue
    return page_vars, attribute, curvalue


def index(request, dataset, analysis, attribute, value=''):
    page_vars, attribute, value = base_page_vars(request, dataset, analysis,
            attribute, value)
    words = []
    tokens = attribute.attributevalue_set.get(value=value).token_count
    attrvalwords = attribute.attributevalueword_set.filter(
            value=value).order_by('-count')
    attrvalwords = attrvalwords.filter(word__ngram=False)
    for attrvalword in attrvalwords[:100]:
        type = attrvalword.word.type
        percent = float(attrvalword.count) / tokens
        w = WordSummary(type, percent)
        w.url = (page_vars['baseurl']+'/'+attribute.name+'/values/'+
                value.value+'/words/'+type)
        words.append(w)
    attrvalngrams = attribute.attributevalueword_set.filter(
            value=value).order_by('-count')
    attrvalngrams = attrvalngrams.filter(word__ngram=True)
    ngrams = []
    for attrvalngram in attrvalngrams[:10]:
        type = attrvalngram.word.type
        percent = float(attrvalngram.count) / tokens
        w = WordSummary(type, percent)
        w.url = (page_vars['baseurl']+'/'+attribute.name+'/values/'+
                value.value+'/words/'+type)
        ngrams.append(w)

    attrvaldocs = attribute.attributevaluedocument_set.filter(value=value)

    topics = []
    analysis = Analysis.objects.get(name=analysis, dataset__name=dataset)
    topic_set = analysis.topic_set.all()
    attrvaltopics = attribute.attributevaluetopic_set.filter(value=value,
            topic__in=topic_set).order_by('-count')
    for attrvaltopic in attrvaltopics[:10]:
        type = attrvaltopic.topic.name
        percent = float(attrvaltopic.count) / tokens
        t = WordSummary(type, percent)
        t.url = '/datasets/%s/analyses/%s/topics/%s' % (
                page_vars['dataset'], page_vars['analysis'],
                attrvaltopic.topic.number)
        topics.append(t)


    page_vars['num_tokens'] = tokens
    page_vars['num_types'] = len(attrvalwords)
    page_vars['num_docs'] = attrvaldocs.count()
    
    page_vars['word_cloud'] = get_word_cloud(words)
    if ngrams:
        page_vars['ngram_cloud'] = get_word_cloud(ngrams)
    page_vars['topic_cloud'] = get_word_cloud(topics, '[', ']')
    
    page_vars['chart_address'] = get_chart(words)
    
    return render_to_response('attribute.html', page_vars)


def word_index(request, dataset, analysis, attribute, value, word):
    page_vars, attribute, value = base_page_vars(request, dataset, analysis,
            attribute, value)
    word = Word.objects.get(dataset__name=dataset, type=word)
    analysis = Analysis.objects.get(dataset__name=dataset, name=analysis)

    documents = word.document_set.filter(attribute=attribute,
            attributevaluedocument__value=value)
    words = []
    for document in documents:
        w = WordSummary(word.type)
        set_word_context(w, document, analysis)
        words.append(w)
        w.url = '%s/%s/values/%s/documents/%d?kwic=%s' % (
                                                          page_vars['baseurl'],
                                                          attribute.name, 
                                                          value.value, 
                                                          document.id,
                                                          word.type)
        w.doc_name = document.filename
        w.doc_id = document.id

    page_vars['words'] = words
    page_vars['breadcrumb'].word(word)
    page_vars['attribute_post_link'] = '/words/%s' % word.type

    return render_to_response('attribute_word.html', page_vars)


def document_index(request, dataset, analysis, attribute, value,
        document):
    page_vars, attribute, value = base_page_vars(request, dataset, analysis,
            attribute, value)
    document = Document.objects.get(dataset__name=dataset, id=document)
    if request.GET and request.GET['kwic']:
        page_vars['text'] = document.text(request.GET['kwic'])
    else:
        page_vars['text'] = document.text()
    page_vars['breadcrumb'].document(document)
    return render_to_response('attribute_document.html', page_vars)



# vim: et sw=4 sts=4
