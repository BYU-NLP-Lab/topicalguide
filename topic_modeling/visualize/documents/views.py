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


from django import forms
from django.shortcuts import render_to_response
from django.template import Context

from topic_modeling.visualize.charts import get_chart
from topic_modeling.visualize.common import BreadCrumb, root_context
from topic_modeling.visualize.common import WordSummary
from topic_modeling.visualize.documents.common import SortDocumentForm
from topic_modeling.visualize.documents.filters import clean_docs_from_session
from topic_modeling.visualize.models import Dataset
from topic_modeling.visualize.models import Document
from topic_modeling.visualize.models import Topic


def base_context(request, dataset, analysis, document):
    context = root_context(dataset, analysis)
    
    context['highlight'] = 'documents_tab'
    context['tab'] = 'document'
    dataset = Dataset.objects.get(name=dataset)
    analysis = dataset.analysis_set.get(name=analysis)

    context['sort_form'] = SortDocumentForm(analysis)

    sort_by = request.session.get('document-sort', 'filename')
    context['sort_form'].fields['sort'].initial = sort_by

    if document:
        document = Document.objects.get(pk=document)
    documents = dataset.document_set
    documents, filter_form, num_pages = clean_docs_from_session(documents,
            request.session, document)
    page_num = request.session.get('document-page', 1)
    context['documents'] = documents
    context['filter'] = filter_form
    context['num_pages'] = num_pages
    context['page_num'] = page_num

    if not document:
        document = context['documents'][0]
    
    context['document_url'] = context['documents_url'] + '/' + str(document.id)
    context['curdocument'] = document
    context['document_text'] = document.text()
    context['document_title'] = document.filename

    context['metrics'] = document.documentmetricvalue_set.all()

    context['breadcrumb'] = BreadCrumb()
    context['breadcrumb'].dataset(dataset)
    context['breadcrumb'].analysis(analysis)
    context['breadcrumb'].document(context['curdocument'])

    return context, analysis, document


def index(request, dataset, analysis, document=""):
    context, analysis, document = base_context(request, dataset, analysis,
            document)
    add_top_topics(request, analysis, document, context)
    add_similarity_measures(request, analysis, document, context)

    return render_to_response('document.html', context)


# Document Widgets
##################

def add_top_topics(request, analysis, document, context):
    topicdocs = document.documenttopic_set.filter(topic__analysis=analysis)
    total = 0
    topics = []
    for topicdoc in topicdocs:
        total += topicdoc.count
    for topicdoc in topicdocs:
        t = WordSummary(topicdoc.topic.name, float(topicdoc.count) / total)
        topics.append(t)
    topics.sort()
    context['chart_address'] = get_chart(topics)


def add_similarity_measures(request, analysis, document, context):
    similarity_measures = analysis.pairwisedocumentmetric_set.all()
    if similarity_measures:
        measure = request.session.get('document-similarity-measure', None)
        if measure:
            measure = similarity_measures.get(name=measure)
        else:
            measure = similarity_measures[0]
        similar_documents = document.pairwisedocumentmetricvalue_originating.\
                select_related().filter(metric=measure).order_by('-value')
        context['similar_documents'] = similar_documents[1:11]
        context['similarity_measures'] = similarity_measures
        context['similarity_measure'] = measure


# vim: et sw=4 sts=4
