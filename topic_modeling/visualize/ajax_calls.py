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

from topic_modeling import anyjson
from topic_modeling.visualize.charts import TopicAttributeChart
from topic_modeling.visualize.charts import TopicMetricChart
from topic_modeling.visualize.common.helpers import get_word_list
from topic_modeling.visualize.common.helpers import paginate_list
#from topic_modeling.visualize.common.ui import WordSummary
from topic_modeling.visualize.models import WordToken, Dataset, Document, WordType, DocumentMetaInfo
#from topic_modeling.visualize.models import Attribute
#from topic_modeling.visualize.models import Topic
#from topic_modeling.visualize.models import Word
from topic_modeling.visualize import sess_key
from topic_modeling.visualize.topics.names import set_current_name_scheme_id
from django.views.decorators.http import require_GET
from topic_modeling.visualize.common.http_responses import JsonResponse
from django.db.models.aggregates import Count



# General ajax calls
####################

@require_GET
def word_in_context(request, dataset, analysis, word, topic=None):
    dataset = Dataset.objects.get(name=dataset)
    word_type = WordType.objects.get(type=word)
    
    if topic is None:
        tokens = WordToken.objects.filter(type=word_type, document__dataset=dataset).all()
    else:
        analysis = dataset.analyses.get(name=analysis)
        topic = analysis.topics.get(number=int(topic))
        tokens = topic.tokens.filter(type=word_type).all()
    
    token = tokens[random.randint(0, len(tokens)-1)]
    doc = token.document
    context = doc.tokens.all()[max(0,token.token_index-5):token.token_index+5]
    
    word_in_context = dict()
    word_in_context['word'] = token.type.type
    word_in_context['left_context'] = ' '.join([x.type.type for x in context[:5]])
    word_in_context['right_context'] = ' '.join([x.type.type for x in context[6:]])
    word_in_context['doc_name'] = doc.filename
    word_in_context['doc_id'] = doc.id
    
    return JsonResponse(word_in_context)
    
@require_GET
def words_in_document_given_topic(request, dataset, analysis, document, topic):
    dataset = Dataset.objects.get(name=dataset)
    document = Document.objects.get(id=int(document), dataset=int(dataset.id))
    analysis = dataset.analyses.get(name=analysis)
    topic = analysis.topics.get(number=int(topic))
    
    words = document.tokens.values('type__type').filter(topics=topic).annotate(count=Count('type__type')).order_by('-count')[0:10]
    return JsonResponse(list(words))

@require_GET
def word_in_contexts_in_document(request, document, word):
    document = Document.objects.get(id=document)
    word_type = WordType.objects.get(type=word)
    tokens = document.tokens.filter(type=word_type)
    tokens = list(tokens)
    
    word_in_contexts = []
    while len(word_in_contexts) < 5 and len(tokens) > 0:
        index = random.randint(0, len(tokens)-1)
        token = tokens.pop(index)
        
        context = document.tokens.all()[max(0, token.token_index - 5):token.token_index + 5 + 1]
        left_context = ' '.join([tok.type.type for tok in context[:5]])
        right_context = ' '.join([tok.type.type for tok in context[5 + 1:]])
        
        word_in_context = dict()
        word_in_context['word'] = token.type.type
        word_in_context['left_context'] = left_context
        word_in_context['right_context'] = right_context
        
        word_in_contexts.append(word_in_context)
    
    return JsonResponse(word_in_contexts)


# Plots tab ajax calls
######################

def attribute_values(request, attribute):
    """
    This is for AJAX calls from the user client to update the list of available
    sub-attributes as the user selects attributes.

    """
    attribute = DocumentMetaInfo.objects.get(pk=attribute)
    values = [av for av in attribute.values.all()]
    #values = attribute.value_set.all()
    return HttpResponse(anyjson.dumps([(v.id, v.value()) for v in values]))

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
    request.session[sess_key(dataset,'attribute-page')] = int(number)
    ret_val = dict()
    values = request.session.get(sess_key(dataset,'values-list'), None)
    if not values:
        attributes = DocumentMetaInfo.objects.filter(
                values__document__dataset__name=dataset, name=attribute).distinct()
        if not attributes:
            raise NotFound
        attribute = attributes[0]
        #attribute = Attribute.objects.get(dataset__name=dataset,
                                          #name=attribute)
        values = attribute.values.distinct()

    num_per_page = request.session.get('attributes-per-page', 20)
    page = int(number)
    values, num_pages, page = paginate_list(values, page, num_per_page)
    uniques = set(val.value() for val in values)
    dcts = [{'value': val} for val in sorted(uniques)]
    ret_val['values'] = dcts #[vars(AjaxValue(val.value())) for val in values]
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
    request.session[sess_key(dataset,'word-page')] = int(number)
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
    request.session[sess_key(dataset,'word-find-base')] = word
    return get_word_page(request, dataset, analysis, 1)

def set_current_name_scheme(request, dataset, name_scheme):
    set_current_name_scheme_id(request, dataset, name_scheme)
    return HttpResponse('Name scheme set to ' + name_scheme)
# vim: et sw=4 sts=4
