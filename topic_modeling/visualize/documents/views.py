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

from topic_modeling.visualize import sess_key
from topic_modeling.visualize.charts import get_chart
from topic_modeling.visualize.common.ui import BreadCrumb
from topic_modeling.visualize.common.views import AnalysisBaseView
from topic_modeling.visualize.common.ui import Tab
from topic_modeling.visualize.common.ui import Widget
from topic_modeling.visualize.common.ui import WordSummary
from topic_modeling.visualize.documents.common import SortDocumentForm
from topic_modeling.visualize.documents.filters import clean_docs_from_session
from topic_modeling.visualize.models import Document, TopicName
from django.shortcuts import get_object_or_404
import logging
logger = logging.getLogger('root')

class DocumentView(AnalysisBaseView):
    template_name = 'documents.html'
    
    def get_context_data(self, request, **kwargs):
        context = super(DocumentView, self).get_context_data(request, **kwargs)
        
        context['highlight'] = 'documents_tab'
        context['tab'] = 'document'
        dataset, analysis = context['dataset'], context['analysis']
        
        if 'document_filters' in kwargs:
            request.session[sess_key(dataset,'document-filters')] = kwargs['document_filters']
    
        context['sort_form'] = SortDocumentForm(analysis)
    
        sort_by = request.session.get(sess_key(dataset,'document-sort'), 'filename')
        context['sort_form'].fields['sort'].initial = sort_by
    
        documents = dataset.documents.all()
        documents, filter_form, num_pages = clean_docs_from_session(documents,
                request.session)
        page_num = request.session.get(sess_key(dataset,'document-page'), 1)
        context['documents'] = documents
        #context['filter'] = filter_form
        context['num_pages'] = num_pages
        context['page_num'] = page_num
    
        try:
            document = get_object_or_404(Document, id=kwargs['document'])
        except KeyError:
            document = context['documents'][0]
    
        context['document_url'] = context['documents_url'] + '/' + str(document.id)
        context['document'] = document
        
        context['view_description'] = document.get_title()
        context['breadcrumb'] = BreadCrumb().item(dataset).item(analysis).item(document)
        
        context['tabs'] = tabs(request, analysis, document)
        
        return context
    


# Document Widgets
##################

# Tabs create groups of widgets.  Each widget must specify a url, a title,
# and whether or not it defaults to visible (only one widget per tab should
# default to visible).
#
# The code that produces widgets also needs to set context variables for
# whatever is needed by the url they specify.

# Text widgets
##############

def tabs(request, analysis, document):
    tabs = []
    tabs.append(text_tab(document))
    tabs.append(similar_documents_tab(request, analysis, document))
    tabs.append(extra_information_tab(analysis, document))
    return tabs

def text_tab(document):
    tab = Tab('Text', 'documents/text')
    tab.add(plain_text_widget(document))
    return tab


def plain_text_widget(document):
    w = Widget("Text", "documents/document_text")
    w['title'] = document.get_title()
    try:
        w['document_text'] = document.text()
    except IOError as e:
        w['document_text'] = '[ error - file not found ]'
        logger.warn('Tried to find a document...and failed: {}'.format(document.full_path))
    return w

# Extra Information Widgets
###########################

def extra_information_tab(analysis, document):
    tab = Tab("Extra Information", 'documents/extra_information')
    tab.add(metrics_widget(document))
    tab.add(metadata_widget(document))
    tab.add(top_topics_widget(analysis, document))
    return tab

def metrics_widget(document):
    w = Widget('Metrics', 'documents/metrics')
    w['metrics'] = document.documentmetricvalues.all()
    return w

def metadata_widget(document):
    w = Widget('Metadata ars Cool', 'documents/metadata_backcompat')
    # FIXME
#    w['docattrval_mgr'] = document.attributevaluedocument_set
    w['metainfovalues'] = document.metainfovalues.all()
    w['metainfos'] = document.metainfovalues.count()
    return w

def top_topics_widget(analysis, document):
    w = Widget('Top Topics', 'documents/top_topics')
    from django.db import connection
    c = connection.cursor()
    c.execute('''SELECT wtt.topic_id, count(*) as cnt
                    FROM visualize_wordtoken wt
                    JOIN visualize_wordtoken_topics wtt
                     on wtt.wordtoken_id = wt.id
                    JOIN visualize_topic t
                     on t.id = wtt.topic_id
                        WHERE t.analysis_id = %d AND wt.document_id = %d
                        GROUP BY wtt.topic_id
                        ORDER BY cnt DESC'''%(analysis.id,document.id))
    rows = c.fetchall()[:10]
    total = 0
    for obj in rows:
        total += obj[1]
    topics = []
    for obj in rows:
        topic_name = TopicName.objects.filter(topic__id=obj[0])[0]
        t = WordSummary(topic_name, float(obj[1]) / total)
        topics.append(t)
    w['chart_address'] = get_chart(topics)
    return w
        
# Similar Documents Widgets
###########################
def similar_documents_tab(request, analysis, document):
    tab = Tab("Similar Documents", 'documents/similar_documents')
    tab.add(similar_documents_widget(request, analysis, document))
    return tab


def similar_documents_widget(request, analysis, document):
    w = Widget("Similar Documents", "documents/similar_documents")
    similarity_measures = analysis.pairwisedocumentmetrics.all()
    if similarity_measures:
        measure = request.session.get(sess_key(analysis.dataset,'similarity_measure'), None)
        if measure:
            measure = similarity_measures.get(name=measure)
        else:
            measure = similarity_measures[0]
        similar_documents = document.pairwisedocumentmetricvalue_originating.\
                select_related().filter(metric=measure).order_by('-value')
        w['similar_documents'] = similar_documents[1:11]
        w['similarity_measures'] = similarity_measures
        w['similarity_measure'] = measure
    return w


# vim: et sw=4 sts=4
