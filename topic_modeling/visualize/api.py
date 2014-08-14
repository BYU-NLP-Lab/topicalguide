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

import sys
from topic_modeling.visualize.models import *
from django.views.decorators.http import require_GET
from django.views.decorators.gzip import gzip_page
from topic_modeling.visualize.common.http_responses import JsonResponse

DEBUG = True

# Turn string s into a list with no repeating values.
def filter_set_to_list(s):
    if s == '':
        result = set()
    elif s == '*':
        return '*'
    elif s.find('%') >= 0: # handle any unencoded unicode
        result = set(s.encode('utf8').replace('%u', '\\u').decode('unicode_escape').split(','))
    else:
        result = set(s.split(','))
    if '' in result:
        result.remove('')
    return list(result)

# Turn string s into an int within the bounds given.
def get_filter_int(low=0, high=sys.maxint):
    def filter_int(s):
        result = int(s)
        if result < low:
            result = low
        if result > high:
            result = high
        return result
    return filter_int
        

# Specify how to filter the incoming request by "key: filter_function" pairs.
OPTIONS_FILTERS = {
    "datasets": filter_set_to_list,
    "analyses": filter_set_to_list,
    "topics": filter_set_to_list,
    "documents": filter_set_to_list,
    "words": filter_set_to_list,
    
    "dataset_attr": filter_set_to_list,
    "analysis_attr": filter_set_to_list,
    "topic_attr": filter_set_to_list,
    "document_attr": filter_set_to_list,
    "word_attr": filter_set_to_list,
    
    "topic_pairwise": filter_set_to_list,
    "top_n_documents": get_filter_int(low=0),
    "top_n_words": get_filter_int(low=0),
    
    "document_continue": get_filter_int(low=0),
    "document_limit": get_filter_int(low=1, high=1000),
    
    "word_metrics": filter_set_to_list,
}

# Filter the incoming get request.
def filter_request(get, filters):
    result = {}
    for key in get:
        if key in filters:
            result[key] = filters[key](get[key])
        else:
            raise Exception("No such value as "+key)
    return result

@gzip_page
@require_GET
def api(request):
    GET = request.GET
    options = filter_request(GET, OPTIONS_FILTERS)
    result = {}
    try:
        if 'datasets' in options:
            result['datasets'] = query_datasets(options)
    except Exception as e:
        result['error'] = str(e)
    return JsonResponse(result)

def query_datasets(options):
    """Gather the information for each dataset listed."""
    datasets = {}
    
    if options['datasets'] == '*':
        datasets_queryset = Dataset.objects.filter(visible=True)
    else:
        datasets_queryset = Dataset.objects.filter(name__in=options['datasets'], visible=True)
    datasets_queryset.select_related()
    
    for dataset in datasets_queryset:
        datasets[dataset.identifier] = dataset.fields_to_dict(options.setdefault('dataset_attr', []))
        
        if 'analyses' in options:
            datasets[dataset.identifier]['analyses'] = query_analyses(options, dataset)
        
    return datasets

def query_analyses(options, dataset):
    analyses = {}
    
    if options['analyses'] == '*':
        analyses_queryset = Analysis.objects.filter(dataset=dataset)
    else:
        analyses_queryset = Analysis.objects.filter(dataset=dataset, name__in=options['analyses'])
    analyses_queryset.select_related()
    
    for analysis in analyses_queryset:
        analyses[analysis.identifier] = analysis.fields_to_dict(options.setdefault('analysis_attr', []))
        if 'topic_count' in options['analysis_attr']:
            analyses[analysis.identifier]['topic_count'] = analysis.topics.count()
        
        if 'topics' in options:
            analyses[analysis.identifier]['topics'] = query_topics(options, dataset, analysis)
        if 'documents' in options:
            analyses[analysis.identifier]['documents'] = query_documents(options, dataset, analysis)
    
    return analyses
    
def query_topics(options, dataset, analysis):
    topics = {}
    if 'topic_attr' in options:
        topic_attr = options['topic_attr']
        
        if options['topics'] == '*':
            topics_queryset = Topic.objects.filter(analysis=analysis)
        else:
            topics_queryset = Topic.objects.filter(analysis=analysis, number__in=options['topics'])
        
        topics_queryset.select_related()
        for topic in topics_queryset:
            attributes = topic.attributes_to_dict(options.setdefault('topic_attr', []), options)
            if 'top_n_words' in topic_attr and 'words' in options and 'top_n_words' in options:
                attributes['words'] = topic.top_n_words(options['words'], top_n=options['top_n_words'])
            if 'top_n_documents' in options:
                attributes['top_n_documents'] = topic.top_n_documents(top_n=options['top_n_documents'])
            topics[topic.identifier] = attributes
    
    return topics

def query_documents(options, dataset, analysis):
    documents = {}
    
    document_attr = options.setdefault('document_attr', [])
    if options['documents'] == '*':
        documents_queryset = Document.objects.filter(dataset=dataset)
    else:
        documents_queryset = Document.objects.filter(dataset=dataset, filename__in=options['documents'])
    
    documents_queryset.order_by('filename')
    
    if 'top_n_topics' in document_attr and \
       options['documents'] == '*' and 'analyses' in options and options['analyses'] != '*':
        from django.db import connection
        c = connection.cursor()
        c.execute('''select wt.document_id, wtt.topic_id, count(*)
                       from visualize_wordtoken wt
                        join visualize_wordtoken_topics wtt
                            on wtt.wordtoken_id = wt.id
                        join visualize_topic t on t.id = wtt.topic_id
                            where t.analysis_id = %d
                            group by wtt.topic_id, wt.document_id'''%(analysis.id,))
        rows = c.fetchall()
        top_n_topics = {}
        for doc_id, topic_id, count in rows:
            if not doc_id in top_n_topics:
                top_n_topics[doc_id] = {}
            top_n_topics[doc_id][topic_id] = count
    
    start = options.setdefault('document_continue', 0)
    limit = options.setdefault('document_limit', 1000)
    documents_queryset = documents_queryset[start:start+limit]
    documents_queryset.select_related()
    for document in documents_queryset:
        attributes = document.attributes_to_dict(document_attr, options)
        documents[document.identifier] = attributes
        if 'top_n_topics' in options['document_attr']:
            if document.id in top_n_topics:
                documents[document.identifier]['topics'] = top_n_topics[document.id]
            else:
                documents[document.identifier]['topics'] = {}
            
    return documents

