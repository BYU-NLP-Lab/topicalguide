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
import time
import json
import itertools
from visualize.models import *
from django.core.cache import cache # Get the 'default' cache.
from django.views.decorators.http import require_GET
from django.views.decorators.gzip import gzip_page
from django.http import HttpResponse
from django.views.decorators.cache import cache_control, patch_cache_control
from django.db import connections
from topicalguide import settings
from utils import reservoir_sample

DEBUG = settings.DEBUG
MAX_DATASETS_PER_REQUEST = 1
MAX_ANALYSES_PER_REQUEST = 1
MAX_DOCUMENTS_PER_REQUEST = 500
MAX_DOCUMENTS_PER_SQL_QUERY = 500

# Turn string s into a list (delimited by commas) with no repeating values.
def filter_set_to_list(s):
    if s == '':
        result = set()
    elif s == '*':
        return '*'
    elif s.find('%') >= 0: # Handle any unencoded unicode.
        result = set(s.encode('utf8').replace('%u', '\\u').decode('unicode_escape').split(','))
    else:
        result = set(s.split(','))
    while '' in result:
        result.remove('')
    return list(result)

# Turn a string into an int within the bounds given.
def get_filter_int(low=-2147483648, high=2147483647):
    def filter_int(s):
        result = int(s)
        if result < low:
            result = low
        if result > high:
            result = high
        return result
    return filter_int

# Specify how to filter the incoming request by "key: filter_function" pairs.
# The filter_function must throw an error on invalid values or return sanitized values.
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
    
    "topic_pairwise": filter_set_to_list,
    "top_n_documents": get_filter_int(low=0),
    "top_n_words": get_filter_int(low=1),
    
    "document_continue": get_filter_int(low=0),
    "document_seed": get_filter_int(),
    "document_limit": get_filter_int(low=1, high=MAX_DOCUMENTS_PER_REQUEST),
    
    "token_indices": filter_set_to_list,
}

# Filter the incoming request.
def filter_request(request_keys, filters):
    result = {}
    for key in request_keys:
        if key in filters:
            result[key] = filters[key](request_keys[key])
        else:
            raise Exception("No such value as "+key)
    return result

# The following line is commented out to prevent browsers from caching requests during development.
# @cache_control(must_revalidate=True, max_age=3600) # Upstream caches must revalidate every hour.
@gzip_page
@require_GET # TODO allow POST for users
def api(request):
    """
    This is the main gateway for retrieving data.
    Only publicly available data is accessible through this api.
    """
    # Variables used to control caching
    path = request.get_full_path()
    options = filter_request(request.GET, OPTIONS_FILTERS)
    request_containing_all = ('datasets' in options and options['datasets'] == '*') or \
                             ('analyses' in options and options['analyses'] == '*')
    DJANGO_CACHE_KEY_LENGTH_LIMIT = 250
    
    if len(path) <= DJANGO_CACHE_KEY_LENGTH_LIMIT and cache.has_key(path): # Check the cache.
        if DEBUG: print('API request hit cache.')
        response = HttpResponse(cache.get(path), content_type='application/json')
    else:
        start_time = time.time()
        
        if DEBUG:
            con = connections['default']
            query_count = len(con.queries)
        
        # Generate the response.
        result = {}
        try:
            if 'datasets' in options:
                result['datasets'] = query_datasets(options)
        except Exception as e:
            result['error'] = str(e)
            if DEBUG:
                raise
        
        # SERVER CACHING
        # Cache the request, if it is time consuming.
        # Don't cache anything requesting all datasets or all analyses.
        # Requests for all datasets/analyses are not cached so new versions can be detected.
        # Requests for all datasets/analyses are limited so this won't cause the server to get bogged down.
        total_time = time.time() - start_time
        
        
        if len(path) <= DJANGO_CACHE_KEY_LENGTH_LIMIT and not request_containing_all:
            # if total_time > 0.5: # if the request takes longer than a second
            cache.set(path, json.dumps(result))
        
        if DEBUG:
            stats = {}
            stats['query_count'] = len(con.queries) - query_count
            stats['queries'] = con.queries[query_count:]
            stats['total_time'] = total_time
            result['server_stats'] = stats
            print('API request hit server.')
        response = HttpResponse(json.dumps(result, indent=4), content_type='application/json')
    
    # CACHING USING HEADERS
    if request_containing_all:
        patch_cache_control(response, private=True)
    else:
        # Set upstream caching. Caches must revalidate every 24 hours.
        patch_cache_control(response, public=True, must_revalidate=True, max_age=60*60*24)
    
    return response

def query_datasets(options):
    """Gather the information for each dataset listed."""
    datasets = {}
    
    # Create the dataset queryset object.
    if options['datasets'] == '*':
        datasets_queryset = Dataset.objects.filter(public=True, visible=True)
    else:
        datasets_queryset = Dataset.objects.filter(name__in=options['datasets'], public=True, visible=True)
    
    # Functions for gathering various attributes.
    DATASET_ATTR = {
        'metadata': lambda dataset: {md.metadata_type.name: md.value() for md in dataset.metadata_values.all()},
        'metrics': lambda dataset: {mv.metric.name: mv.value for mv in dataset.metric_values.all()},
        'document_count': lambda dataset: int(dataset.metric_values.filter(metric__name='Document Count')[0].value),
        'analysis_count': lambda dataset: dataset.analyses.count(),
        'document_metadata_types': lambda dataset: dataset.get_document_metadata_types(),
    }
    
    # Get the list of attributes the user wants.
    dataset_attr = options.setdefault('dataset_attr', [])
    
    # These perform database queries in bulk to avoid hitting the database multiple times.
    if 'metadata' in dataset_attr:
        datasets_queryset = datasets_queryset.prefetch_related('metadata_values', 'metadata_values__metadata_type')
    if 'metrics' in dataset_attr or 'document_count' in dataset_attr:
        datasets_queryset = datasets_queryset.prefetch_related('metric_values', 'metric_values__metric')
    
    # Gather the requested information.
    for dataset_db in datasets_queryset:
        attributes = {}
        for attr in dataset_attr:
            if attr in DATASET_ATTR:
                attributes[attr] = DATASET_ATTR[attr](dataset_db)
        
        if 'analyses' in options:
            attributes['analyses'] = query_analyses(options, dataset_db)
        
        datasets[dataset_db.name] = attributes
        
    return datasets

def query_analyses(options, dataset_db):
    analyses = {}
    
    if options['analyses'] == '*':
        analyses_queryset = Analysis.objects.filter(dataset=dataset_db)
    else:
        analyses_queryset = Analysis.objects.filter(dataset=dataset_db, name__in=options['analyses'])
    analyses_queryset.select_related()
    
    ANALYSIS_ATTR = {
        'metadata': lambda analysis_db: {md.metadata_type.name: md.value() for md in analysis_db.metadata_values.all()},
        'metrics': lambda analysis_db: {mv.metric.name: mv.value for mv in analysis_db.metric_values.all()},
        'topic_count': lambda analysis_db: analysis_db.topics.count(),
    }
    
    analysis_attr = options.setdefault('analysis_attr', [])
    
    # Prefetch needed data to reduce number of database queries
    if 'metadata' in analysis_attr:
        analyses_queryset = analyses_queryset.prefetch_related('metadata_values', 'metadata_values__metadata_type')
    if 'metrics' in analysis_attr:
        analyses_queryset = analyses_queryset.prefetch_related('metric_values', 'metric_values__metric')
    
    # Gather information about each analysis
    for analysis_db in analyses_queryset:
        # Gather basic attributes
        attributes = {}
        for attr in analysis_attr:
            if attr in ANALYSIS_ATTR:
                attributes[attr] = ANALYSIS_ATTR[attr](analysis_db)
        
        # Gather complex attributes
        if options['analyses'] != '*' and options['datasets'] != '*':
            if 'topics' in options:
                attributes['topics'] = query_topics(options, dataset_db, analysis_db)
            if 'documents' in options:
                attributes['documents'] = query_documents(options, dataset_db, analysis_db)
        
        analyses[analysis_db.name] = attributes
    
    return analyses
    
def query_topics(options, dataset_db, analysis_db):
    topics = {}
    if 'topic_attr' in options:
        if options['topics'] == '*':
            topics_queryset = analysis_db.topics.all();
        else:
            topics_queryset = analysis_db.topics.filter(number__in=options['topics'])
        
        TOPIC_ATTR = {
            'metadata': lambda topic: {md.metadata_type.name: md.value() for md in topic.metadata_values.all()},
            'metrics': lambda topic: {mv.metric.name: mv.value for mv in topic.metric_values.all()},
            'names': lambda topic: {name.name_scheme.name: name.name for name in topic.names.all()},
        }
        
        topic_attr = options.setdefault('topic_attr', [])
        
        if 'metadata' in topic_attr:
            topics_queryset = topics_queryset.prefetch_related('metadata_values', 'metadata_values__metadata_type')
        if 'metrics' in topic_attr:
            topics_queryset = topics_queryset.prefetch_related('metric_values', 'metric_values__metric')
        if 'pairwise' in topic_attr:
            topics_queryset = topics_queryset.prefetch_related('originating_metric_values', 'originating_metric_values__metric', 'originating_metric_values__ending_topic')
        if 'names' in topic_attr:
            topics_queryset = topics_queryset.prefetch_related('names', 'names__name_scheme')
        
        for topic_db in topics_queryset:
            attributes = {}
            
            for attr in topic_attr:
                if attr in TOPIC_ATTR:
                    attributes[attr] = TOPIC_ATTR[attr](topic_db)
            
            if 'pairwise' in topic_attr:
                attributes['pairwise'] = topic_db.get_pairwise_metrics(options)
            if 'top_n_words' in topic_attr and 'words' in options and 'top_n_words' in options:
                attributes['words'] = topic_db.top_n_words(options['words'], top_n=options['top_n_words'])
            if 'top_n_documents' in options:
                attributes['top_n_documents'] = topic_db.top_n_documents(top_n=options['top_n_documents'])
            if 'words' in options and options['words'] != '*' and 'word_tokens' in topic_attr:
                attributes['word_tokens'] = topic_db.get_word_tokens(options['words'])
            if 'word_token_documents_and_locations' in topic_attr and 'documents' in options:
                attributes['word_token_documents_and_locations'] = topic_db.get_word_token_documents_and_locations(options['documents'])
            
            topics[topic_db.number] = attributes
    
        # Two attempts at getting token counts faster by using one or two queries.
        #~ if 'top_n_words' in topic_attr and 'words' in options and options['words'] == '*' and 'top_n_words' in options:
            #~ topics_queryset = topics_queryset.prefetch_related('tokens', 'tokens__word_type')
            #~ temp = topics_queryset.values('number', 'tokens__word_type__word').annotate(count=Count('tokens__word_type__word')).order_by('-count')
            #~ topics['temp'] = [[value['number'], value['tokens__word_type__word'], value['count']] for value in temp]
        #~ if 'top_n_words' in topic_attr and 'words' in options and 'top_n_words' in options:
            #~ words = options['words']
            #~ top_n = options['top_n_words']
            #~ topic_words = analysis_db.tokens.values('topics__number', 'word_type__word').annotate(count=Count('word_type__word'))
            #~ if words != '*':
                #~ topic_words = topic_words.filter(word_type__word__in=words)
            #~ topic_words = topic_words.order_by('topics__number', '-count')
            #~ topic_top_n_words = {}
            #~ topic_counts = {}
            #~ for row in topic_words:
                #~ topic_num = row['topics__number']
                #~ if topic_num not in topic_top_n_words:
                    #~ topic_top_n_words[topic_num] = {}
                    #~ topic_counts[topic_num] = 0
                #~ if topic_counts[topic_num] < top_n:
                    #~ topic_top_n_words[topic_num][row['word_type__word']] = {'token_count': row['count']}
                    #~ topic_counts[topic_num] += 1
    
    return topics

def query_documents(options, dataset_db, analysis_db):
    documents = {}
    
    if options['documents'] == '*':
        documents_queryset = dataset_db.documents.all()
    else:
        documents_queryset = dataset_db.documents.filter(filename__in=options['documents'])
    
    DOCUMENT_ATTR = {
        'metadata': lambda doc: {md.metadata_type.name: md.value() for md in doc.metadata_values.all()},
        'metrics': lambda doc: {mv.metric.name: mv.value for mv in itertools.chain(doc.metric_values.all(), doc.document_analysis_metric_values.all()) 
                                if type(mv) is not DocumentAnalysisMetricValue or mv.analysis_id==analysis_db.id},
        'text': lambda doc: doc.get_content() if dataset_db.public_documents else "Document text unavailable.",
    }
    
    document_attr = options.setdefault('document_attr', [])
    
    if 'metadata' in document_attr:
        documents_queryset = documents_queryset.prefetch_related('metadata_values', 'metadata_values__metadata_type')
    if 'metrics' in document_attr:
        documents_queryset = documents_queryset.prefetch_related('metric_values', 'metric_values__metric')
        documents_queryset = documents_queryset.prefetch_related('document_analysis_metric_values', 'document_analysis_metric_values__metric')
    if 'text' in document_attr or 'kwic' in document_attr:
        documents_queryset = documents_queryset.prefetch_related('dataset')
    
    
    # WARNING: because of the query chaining to prevent too large of queries
    #          this next section of code must come after any prefetching
    limit = options.setdefault('document_limit', MAX_DOCUMENTS_PER_REQUEST)
    doc_count = dataset_db.documents.count()
    if doc_count > limit: # Restrict the documents to a certain range
        if 'document_seed' in options:
            sample_indices = reservoir_sample(limit, doc_count, options['document_seed'])
            documents['sample_indices'] = sample_indices
            i = 0
            chunk_size = MAX_DOCUMENTS_PER_SQL_QUERY
            chain = []
            while i < len(sample_indices):
                chain.append(documents_queryset.filter(index__in=sample_indices[i: i+chunk_size]))
                i += chunk_size
            documents_queryset = itertools.chain(*chain)
        else:
            start = options.setdefault('document_continue', 0)
            start = start % doc_count
            i = start
            chunk_size = MAX_DOCUMENTS_PER_SQL_QUERY
            chain = []
            while i < start + limit:
                chain.append(documents_queryset.filter(index__range=(i, i + chunk_size)))
                i += chunk_size
            documents_queryset = itertools.chain(*chain)
    
    # Must come after range filtering since similar variables are used.
    if 'top_n_topics' in document_attr and \
       options['documents'] == '*' and 'analyses' in options and options['analyses'] != '*':
        query = analysis_db.tokens.values_list('document', 'topics__number').annotate(count=Count('document'))
        if doc_count > limit:
            if 'document_seed' in options:
                i = 0
                chunk_size = MAX_DOCUMENTS_PER_SQL_QUERY
                chain = []
                while i < len(sample_indices):
                    chain.append(query.filter(document__index__in=sample_indices[i: i+chunk_size]))
                    i += chunk_size
                query = itertools.chain(*chain)
            else:
                i = start
                chunk_size = MAX_DOCUMENTS_PER_SQL_QUERY
                chain = []
                while i < start+limit:
                    chain.append(query.filter(document__index__range=(i, i+chunk_size)))
                    i += chunk_size
                query = itertools.chain(*chain)
        
        top_n_topics = {}
        topics_db = {topic.id: topic.number for topic in analysis_db.topics.all()}
        for doc_id, topic_id, count in query:
            if not doc_id in top_n_topics:
                top_n_topics[doc_id] = {}
            top_n_topics[doc_id][topic_id] = count
    
    
    for document_db in documents_queryset:
        attributes = {}
        
        for attr in document_attr:
            if attr in DOCUMENT_ATTR:
                attributes[attr] = DOCUMENT_ATTR[attr](document_db)
        
        if 'metrics' in document_attr:
            attributes['metrics']['Length'] = document_db.length
        if 'top_n_topics' in options['document_attr'] and \
           options['documents'] == '*' and 'analyses' in options and options['analyses'] != '*':
            if document_db.id in top_n_topics:
                attributes['topics'] = top_n_topics[document_db.id]
            else:
                attributes['topics'] = {}
        if 'kwic' in document_attr and 'token_indices' in options:
            if dataset_db.public_documents:
                attributes['kwic'] = document_db.get_key_word_in_context(options['token_indices'])
            else:
                attributes['kwic'] = {}
        if 'word_token_topics_and_locations' in document_attr and 'words' in options:
            if dataset_db.public_documents:
                attributes['word_token_topics_and_locations'] = document_db.get_word_token_topics_and_locations(analysis_db, options['words'])
            else:
                attributes['word_token_topics_and_locations'] = {}
        
        documents[document_db.filename] = attributes
                
    return documents

