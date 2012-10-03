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
from topic_modeling.visualize.models import DocumentMetaInfo#, Attribute
from topic_modeling.visualize.models import Document, DocumentMetaInfoValue, WordToken
#from topic_modeling.visualize.models import Value
from topic_modeling.visualize.models import WordType
from topic_modeling.visualize import sess_key
from django.db.models.aggregates import Count

from backend import c

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
        context['attributes'] = DocumentMetaInfo.objects.filter(values__document__dataset=dataset).distinct()
#        context['attributes'] = dataset.attribute_set.all()
        if attribute:
            ## why do we have duplicates??? in the db
            attributes_ = DocumentMetaInfo.objects.filter(
                    values__document__dataset=dataset, name=attribute).distinct()
            if not attributes_:
                raise NotFound
            attribute = attributes_[0]
            #attribute = get_object_or_404(DocumentMetaInfo, values__document__dataset=dataset,
                    #name=attribute)
            prev_attribute = request.session.get(sess_key(dataset,'attribute-name'), '')
            if prev_attribute != attribute.name:
                request.session['attribute-name'] = attribute.name
                request.session['attribute-page'] = 1
        else:
            request.session['attribute-page'] = 1
            attribute = context['attributes'][0]
    
        context['attribute'] = attribute
    
        values = attribute.values.all()
        page_num = request.session.get(sess_key(dataset,'attribute-page'), 1)
        num_per_page = request.session.get('attributes-per-page', 20)
        values, num_pages, page_num = paginate_list(values, page_num, num_per_page)
        context['num_pages'] = num_pages
        context['page_num'] = page_num
        context['values'] = [v.value for v in values]
    
        if value:
            ## remove once we've killed the crazy typeness
            tmp = attribute.values.all()[0]
            getvals = {tmp.type() + '_value': value, 'info_type': attribute}
            ## TODO: why can we have this return multiple objects?
            value = DocumentMetaInfoValue.objects.filter(**getvals)
            if not value:
                raise NotFound
            value = value[0]
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
        mi = DocumentMetaInfo.objects.get(name=kwargs['attribute'])
        mivs = mi.values.filter()
        documents = dataset.docs.filter(metainfovalues)
        
        word = WordType.objects.get(type=kwargs['word'])
        documents = word.document_set.filter(attribute=attribute,#FIXME
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
    
    token_count = WordToken.objects.filter(
        document__metainfovalues__info_type=attribute,
        document__metainfovalues=value).count()
#    token_count = attribute.attributevalue_set.get(value=value).token_count
    words = get_words(attribute, value, attributes_url, token_count)
    
    value_type = attribute.values.all()[0].type() + '_value'
    tab.add(metrics_widget(analysis.dataset, attribute, value, value_type, token_count))
    tab.add(top_words_chart_widget(words))
    tab.add(word_cloud_widget(words))
#    ngram_widget = ngram_word_cloud_widget(attribute, value, attributes_url, token_count)
#    if ngram_widget: tab.add(ngram_widget)
    tab.add(topic_cloud_widget(analysis, attribute, value, analysis_url, token_count))
    
    return tab

#FIXME Only works with text values
def get_attrvalwords(attribute, value):
    attrname = value.type() + '_value'
    dct = {attrname: value.value()}
    return attribute.values.filter(**dct).values('document__tokens__type__type')\
        .annotate(count=Count(attrname)).order_by('-count')
#    attrvalwords = attribute.attributevalueword_set.filter(
#            value=value).order_by('-count')
#    attrvalwords = attrvalwords.filter(word__ngram=False)
#    return attrvalwords

def filterout(words, stopwords, max=-1):
    count = 0
    for word in words:
        if not word['document__tokens__type__type'] in stopwords:
            count+=1
            yield word
            if count >= max:
                return

def get_words(attribute, value, attributes_url, token_count):
    words = []
    attrvalwords = get_attrvalwords(attribute, value)
    stopwords = open(c['stopwords_file']).read().split('\n')
    for attrvalword in filterout(attrvalwords, stopwords, 100):
        type = attrvalword['document__tokens__type__type']
        percent = float(attrvalword['count']) / token_count
        w = WordSummary(WordType.objects.get(type=type), percent)
        w.url = (attributes_url + '/' + attribute.name + '/values/' + 
                str(value.value()) + '/words/' + type)
        words.append(w)
    return words

import datetime, time
def attr_type(value):
    if type(value) == int:
        return 'int_'
    elif type(value) == float:
        return 'float_'
    elif isinstance(value, basestring):
        return 'text_'
    elif isinstance(value, datetime.datetime):
        return 'datetime_'
    elif isinstance(value, time.struct_time):
        return 'datetime_'
    elif type(value) == bool:
        return 'bool_'
    else:
        raise Exception('Bad attr type: %s' % value)
    

def get_topics(analysis, attribute, value, analysis_url, token_count):
    topics = []
    topic_set = analysis.topics.all()

    '''I want to count the number of wordtokens that have a certain  documents
    that have the metaattribute "value"'''
    data = []
    for topic in topic_set:
        count = WordToken.objects.filter(document__metainfovalues=value, topics=topic).count()
        data.append((count, topic))
    data.sort()
    # vtype = attr_type(value)
    # attrvalue = getattr(value, vtype+'_value')
    # mytopics = analysis.topics.filter(topics__tokens__
    # attrvaltopics = attribute.values.filter(value=value)
    # attrvaltopics = attribute.attributevaluetopic_set.filter(value=value,
            # topic__in=topic_set).order_by('-count')
    for count, topic in list(reversed(data))[:10]:
        # type = topic.name
        topicName = topic.names.filter(name_scheme__analysis=analysis).all()[0]
        percent = float(count) / token_count
        t = WordSummary(topicName, percent)
        t.url = analysis_url + '/topics/%s' % (topic.number)
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

def metrics_widget(dataset, attribute, value, value_type, token_count):
    w = Widget('Metrics', 'attributes/metrics')
    w['num_types'] = WordType.objects.filter(**{
        'tokens__document__metainfovalues__info_type': attribute,
        'tokens__document__metainfovalues__' + value_type: value.value()
        }).distinct().count()
    w['num_docs'] = dataset.documents.filter(**{
        'metainfovalues__info_type': attribute,
        'metainfovalues__' + value_type: value.value()
        }).count()
#    attrvaldocs = attribute.attributevaluedocument_set.filter(value=value)
#    attrvalwords = get_attrvalwords(attribute, value)
    w['num_tokens'] = token_count
#    w['num_types'] = attrvalwords.count()
#    w['num_docs'] = attrvaldocs.count()
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
