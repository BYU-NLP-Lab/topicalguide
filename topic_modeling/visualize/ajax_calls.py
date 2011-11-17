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
from topic_modeling.visualize.common.ui import WordSummary
from topic_modeling.visualize.models import Analysis
from topic_modeling.visualize.models import Attribute
from topic_modeling.visualize.models import Topic
from topic_modeling.visualize.models import Word



# General ajax calls
####################

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
    else:
        raise ValueError("Format '%' is not supported" % fmt)

def topic_attribute_csv(request, attribute, topic, value):
    chart_parameters = {'attribute': attribute, 'topic': topic, 'value': value}
    if request.GET.get('frequency', False):
        chart_parameters['frequency'] = 'True'
    if request.GET.get('histogram', False):
        chart_parameters['histogram'] = 'True'
    chart = TopicAttributeChart(chart_parameters)
    return HttpResponse(chart.get_csv_file(), mimetype="text/csv")

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
    values, num_pages, _ = paginate_list(values, page, num_per_page)
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
    words, num_pages, _ = paginate_list(words, page, num_per_page)

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
