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

import random

from django.http import HttpResponse
from django.shortcuts import get_object_or_404

from topic_modeling import anyjson
from topic_modeling.visualize.common.http_responses import JsonResponse
from topic_modeling.visualize.charts import TopicAttributeChart
from topic_modeling.visualize.charts import TopicMetricChart
from topic_modeling.visualize.common.helpers import get_word_list
from topic_modeling.visualize.common.helpers import paginate_list
from topic_modeling.visualize.common.ui import WordSummary
from topic_modeling.visualize.models import Analysis, Document, \
    PairwiseDocumentMetric, PairwiseTopicMetric
from topic_modeling.visualize.models import Attribute
from topic_modeling.visualize.models import AttributeValueDocument
from topic_modeling.visualize.models import Dataset
from topic_modeling.visualize.models import Value
from topic_modeling.visualize.models import Topic
from topic_modeling.visualize.models import Word



# General ajax calls
####################


def topic_token_counts(request, dataset, analysis, docId, cmpTopicId=None, attribute_name = u"author_name"):
    '''
        Returns a JSON representation of a treemap of depth 1. For each child of the parent node, we return its name,
        id, size, and similarity to the topic with id cmpTopicId.
        
        If no cmpTopicId is given, then we use the topic with the largest number of tokens in this document.
        This default behavior may be changed in the future.
    '''
    
    analysis = get_object_or_404(Analysis, dataset__name=dataset, name=analysis)
    document = analysis.dataset.document_set.get(id=docId);
    attr = AttributeValueDocument.objects.get(document=document, attribute__name=attribute_name)
    
    # choose a compared topic
    if cmpTopicId is None:
        maxTopicId = document.documenttopic_set.order_by('-count')[0].topic.id
    else:
        maxTopicId = cmpTopicId;
        
    # add size factors, #token and similarity
    children = []        
    for dt in document.documenttopic_set.filter(topic__analysis=analysis).all():
        child = {"name": str(dt.topic.name), "size" : dt.count, "similarity" : topics_similarity(dt.topic_id, maxTopicId), "tid":dt.topic_id}
        children.append(child)

    return JsonResponse({'name':str(attr.value), 'children':children})
    
def document_token_counts(request, dataset, attribute_name = u"author_name"):
    '''
        Returns a JSON representation of a topic treemap of depth 1 given an attribute.
        
        The root of the tree is the dataset, the first layer  
    '''
    
    dataset = get_object_or_404(Dataset, name=dataset)
    
    # get the actual instances      
    attr = get_object_or_404(Attribute, dataset__name=dataset, name=attribute_name)
    
    value_nodes = []                
    for value in attr.value_set.all():
        
        # get all document ids in this attribute
        docIds = [attrvaldoc.document_id for attrvaldoc in value.attributevaluedocument_set.all()]
        
        value_node = {}
        value_node["isDoc"] = 1 # Sets color
        value_node["children"] = [{"name":str(value), 
                              "size":attr.attributevalue_set.get(value=value).token_count, 
                              "child_doc_ids":docIds}]
        value_nodes.append(value_node)
    
    return JsonResponse({'name':str(dataset.readable_name), 'children':value_nodes})        

def documents_similarity(doc1Id, doc2Id):
    doc1 = Document.objects.get(id=doc1Id)
    doc2 = Document.objects.get(id=doc2Id)
    # [1] topic Correlation
    return float(PairwiseDocumentMetric.objects.all()[1].pairwisedocumentmetricvalue_set.get(document1=doc1, document2=doc2).value)

def topics_similarity(tid1, tid2):
    t1 = Topic.objects.get(id=tid1)
    t2 = Topic.objects.get(id=tid2)
    # [0] document correlation
    return round(float(PairwiseTopicMetric.objects.all()[0].pairwisetopicmetricvalue_set.get(topic1=t1, topic2=t2).value), 3)


def word_in_context(request, dataset, analysis, word, topic=None):
    analysis = Analysis.objects.get(name=analysis, dataset__name=dataset)
    w = Word.objects.get(dataset__name=dataset, type=word)
    word_context = WordSummary(word)

    if topic is None:
        docset = w.documentword_set.all()
    else:
        topic = Topic.objects.get(analysis=analysis, number=topic)
        docset = topic.documenttopicword_set.filter(word=w)

    num_docs = len(docset)
    d = docset[random.randint(0, num_docs - 1)]

    word_context.left_context, word_context.word, word_context.right_context \
 = d.document.get_context_for_word(word, analysis, topic.number if topic else None)

    word_context.doc_name = d.document.filename
    word_context.doc_id = d.document.id
    return HttpResponse(anyjson.dumps(vars(word_context)))


# Plots tab ajax calls
######################

def attribute_values(request, attribute):
    """
    This is for AJAX calls from the user client to update the list of available
    sub-attributes as the user selects attributes.

    """
    attribute = Attribute.objects.get(pk=attribute)
    values = [av.value for av in attribute.attributevalue_set.select_related().order_by('value__value')]
    #values = attribute.value_set.all()
    return HttpResponse(anyjson.dumps([(v.id, v.value) for v in values]))

def topic_attribute_plot(request, attribute, topic, value):
    fmt = request.GET['fmt'] if 'fmt' in request.GET else 'json'
    if fmt == 'json':
        chart_parameters = {'attribute': attribute, 'topic': topic, 'value': value}
        if request.GET.get('frequency', False):
            chart_parameters['frequency'] = 'True'
        if request.GET.get('histogram', False):
            chart_parameters['histogram'] = 'True'
        chart = TopicAttributeChart(chart_parameters)

        return HttpResponse(anyjson.dumps(chart.get_source_data()),
                            content_type='application/javascript; charset=utf8')
    elif fmt == 'png':
        chart_parameters = {'attribute': attribute, 'topic': topic, 'value': value}
        if request.GET.get('frequency', False):
            chart_parameters['frequency'] = 'True'
        if request.GET.get('histogram', False):
            chart_parameters['histogram'] = 'True'
        chart = TopicAttributeChart(chart_parameters)
        return HttpResponse(chart.get_chart_image(), mimetype="image/png")
    elif fmt == 'csv':
        chart_parameters = {'attribute': attribute, 'topic': topic, 'value': value}
        if request.GET.get('frequency', False):
            chart_parameters['frequency'] = 'True'
        if request.GET.get('histogram', False):
            chart_parameters['histogram'] = 'True'
        chart = TopicAttributeChart(chart_parameters)
        return HttpResponse(chart.get_csv_file(), mimetype="text/csv")
    else:
        raise ValueError("Format '%' is not supported" % fmt)


def topic_metric_plot(request, dataset, analysis, metric):
    chart_parameters = {'dataset': dataset, 'analysis': analysis}
    first, second = metric.split('.')
    chart_parameters['first_metric'] = first
    chart_parameters['second_metric'] = second
    if request.GET.get('linear_fit', False):
        chart_parameters['linear_fit'] = 'True'
    chart = TopicMetricChart(chart_parameters)

    return HttpResponse(chart.get_chart_image(), mimetype="image/png")


# Attributes tab ajax calls
###########################

def get_attribute_page(request, dataset, analysis, attribute, number):
    request.session['attribute-page'] = int(number)
    ret_val = dict()
    values = request.session.get('values-list', None)
    if not values:
        attribute = Attribute.objects.get(dataset__name=dataset,
                                          name=attribute)
        values = attribute.value_set.all()

    num_per_page = request.session.get('attributes-per-page', 20)
    page = int(number)
    values, num_pages, page = paginate_list(values, page, num_per_page)
    ret_val['values'] = [vars(AjaxValue(val.value)) for val in values]
    ret_val['num_pages'] = num_pages
    ret_val['page'] = page
    return HttpResponse(anyjson.dumps(ret_val))


class AjaxValue(object):
    def __init__(self, value):
        self.value = value


# Word tab ajax calls
##########################

class AjaxWord:
    def __init__(self, type):
        self.type = type


def get_word_page(request, dataset, analysis, number):
    request.session['word-page'] = int(number)
    ret_val = dict()

    words = get_word_list(request, dataset)

    num_per_page = request.session.get('words-per-page', 30)
    page = int(number)
    words, num_pages, page = paginate_list(words, page, num_per_page)

    ret_val['words'] = [vars(AjaxWord(word.type)) for word in words]
    ret_val['num_pages'] = num_pages
    ret_val['page'] = page
    return HttpResponse(anyjson.dumps(ret_val))


def update_word_page(request, dataset, analysis, word):
    request.session['word-find-base'] = word
    return get_word_page(request, dataset, analysis, 1)

def set_current_name_scheme(request, name_scheme):
    request.session['current_name_scheme_id'] = name_scheme
    return HttpResponse('Name scheme set to ' + name_scheme)
# vim: et sw=4 sts=4
