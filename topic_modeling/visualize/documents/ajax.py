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

from topic_modeling.visualize.common import FilterForm
from topic_modeling.visualize.documents.filters import clean_docs_from_session
from topic_modeling.visualize.documents.filters import get_doc_filter_by_name
from topic_modeling.visualize.documents.filters import possible_document_filters
from topic_modeling.visualize.models import Analysis
from topic_modeling.visualize.models import Dataset
from topic_modeling.visualize.models import Document
from topic_modeling.profiler import profile

import simplejson

# General and Sidebar stuff
###########################

def get_document_page(request, dataset, analysis, document, number):
    request.session['document-page'] = int(number)
    ret_val = dict()
    documents = request.session.get('documents-list', None)
    if not documents:
        documents = Document.objects.filter(dataset__name=dataset)
    page = int(number)
    documents, filter_form, num_pages = clean_docs_from_session(documents,
            request.session)
    ret_val['documents'] = [vars(AjaxDocument(doc)) for doc in documents]
    ret_val['num_pages'] = num_pages
    ret_val['page'] = page
    return HttpResponse(simplejson.dumps(ret_val))


def document_ordering(request, dataset, analysis, order_by):
    request.session['document-sort'] = order_by
    request.session['document-page'] = 1
    ret_val = dict()
    documents = Document.objects.filter(dataset__name=dataset)
    docs, _, num_pages = clean_docs_from_session(documents, request.session)
    ret_val['documents'] = [vars(AjaxDocument(doc)) for doc in docs]
    ret_val['num_pages'] = num_pages
    ret_val['page'] = 1
    return HttpResponse(simplejson.dumps(ret_val))


# Widgets
#########

def similar_documents(request, dataset, analysis, document, measure):
    ret_val = dict()
    request.session['document-similarity-measure'] = measure
    dataset = Dataset.objects.get(name=dataset)
    analysis = Analysis.objects.get(dataset=dataset, name=analysis)
    document = dataset.document_set.get(pk=document)
    measure = analysis.pairwisedocumentmetric_set.get(name=measure)
    similar_documents = document.pairwisedocumentmetricvalue_originating.\
            select_related().filter(metric=measure).order_by('-value')[1:11]
    documents = [d.document2 for d in similar_documents]
    values = [d.value for d in similar_documents]
    ret_val['values'] = values
    ret_val['documents'] = [vars(AjaxDocument(doc)) for doc in documents]
    return HttpResponse(simplejson.dumps(ret_val))


# Filters
#########

def new_document_filter(request, dataset, analysis, document, name):
    dataset = Dataset.objects.get(name=dataset)
    analysis = Analysis.objects.get(dataset=dataset, name=analysis)
    filters = request.session.get('document-filters', [])
    filter_form = FilterForm(possible_document_filters())
    id = 0
    for filter in filters:
        filter.id = id
        filter_form.add_filter(filter)
        id += 1
    new_filter = get_doc_filter_by_name(name)(dataset, analysis, id)
    filter_form.add_filter(new_filter)
    filters.append(new_filter)
    request.session['document-filters'] = filters
    return HttpResponse(filter_form.__unicode__())


def remove_document_filter(request, dataset, analysis, document, number):
    request.session['document-filters'].pop(int(number))
    request.session.modified = True
    return filtered_documents_response(request, dataset, analysis)


def filtered_documents_response(request, dataset, analysis):
    dataset = Dataset.objects.get(name=dataset)
    documents = dataset.document_set
    request.session['document-page'] = 1
    documents, filter_form, num_pages = clean_docs_from_session(documents,
            request.session)
    ret_val = dict()
    ret_val['filter_form'] = filter_form.__unicode__()
    ret_val['documents'] = [vars(AjaxDocument(doc)) for doc in documents]
    ret_val['num_pages'] = num_pages
    ret_val['page'] = request.session.get('document-page', 1)
    return HttpResponse(simplejson.dumps(ret_val))


def update_document_topic_filter(request, dataset, analysis, document, number,
        topic):
    filter = request.session['document-filters'][int(number)]
    if topic == 'None':
        filter.current_topic = None
    else:
        filter.current_topic = topic
    filter.remake_form()
    request.session.modified = True
    return filtered_documents_response(request, dataset, analysis)


def update_document_attribute_filter(request, dataset, analysis, document,
        number, attribute, value=None):
    filter = request.session['document-filters'][int(number)]
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
    return filtered_documents_response(request, dataset, analysis)


def update_document_metric_filter(request, dataset, analysis, document, number,
        metric, comp=None, value=None):
    filter = request.session['document-filters'][int(number)]
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
    return filtered_documents_response(request, dataset, analysis)


class AjaxDocument(object):
    def __init__(self, document):
        self.name = str(document)
        self.id = document.id


# vim: et sw=4 sts=4
