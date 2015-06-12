
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
from __future__ import division, print_function, unicode_literals
import sys
import time
import json
import itertools
from git import Repo
from visualize.models import *
from visualize.utils import reservoir_sample
from visualize.api_utilities import get_list_filter, filter_csv_to_list, \
    get_filter_int, filter_nothing, filter_request, get_filter_csv_to_tuple, \
    get_filter_csv_to_numeric_tuple, filter_csv_to_list_keep_order, filter_to_json

MAX_DOCUMENTS_PER_REQUEST = 500
MAX_DOCUMENTS_PER_SQL_QUERY = 500

# Get function to turn a csv string into a list and check that the arguments are valid.
def get_list_filter(allowed_values, allow_star=False):
    allowed_values = set(allowed_values)
    def list_filter(s):
        if allow_star and s == '*':
            return '*'
        result = set(s.split(','))
        if '' in result:
            result.remove('')
        for r in result:
            if r not in allowed_values:
                raise Exception('The value "%s" is not recognized.'%(r,))
        return list(result)
    return list_filter
        
# Turn string s into a list (delimited by commas) with no repeating values.
# Treat '*' as an exception since '*' means everything.
def filter_csv_to_list(s):
    if s == '':
        result = set()
    elif s == '*':
        return '*'
    elif s.find('%') >= 0: # Handle any unencoded unicode.
        result = set(s.encode('utf8').replace('%u', '\\u').decode('unicode_escape').split(','))
    else:
        result = set(s.split(','))
    if '' in result:
        result.remove('')
    return list(result)

# Get function to turn a string into an int within the bounds given.
def get_filter_int(low=-2147483648, high=2147483647):
    def filter_int(s):
        result = int(s)
        if result < low:
            result = low
        if result > high:
            result = high
        return result
    return filter_int

# A do-nothing filter.
def filter_nothing(arg):
    return arg

# Specify how to filter the incoming request by "key: filter_function" pairs.
# The filter_function must throw an error on invalid values or return sanitized values.
OPTIONS_FILTERS = {
    'server': get_list_filter(['version', 'api_version', 'max_documents_per_request', 'license_url', 'terms', 'metadata_types', 'metadata_meanings'], allow_star=True),
    
    'version': filter_nothing,

    # how to filter
    'datasets': filter_csv_to_list,
    'analyses': filter_csv_to_list,
    'topics': filter_csv_to_list,
    'documents': filter_csv_to_list,
    'words': filter_csv_to_list,
    'metadata_name': filter_nothing,
    'metadata_value': filter_nothing,
    'metadata_range': get_filter_csv_to_numeric_tuple(2),
    
    # what data to gather
    'dataset_attr': get_list_filter(['metadata', 'metrics', 'document_count', 'analysis_count', 'document_metadata_types', 'document_metadata_ordinals', 'document_metadata_meanings']),
    'analysis_attr': get_list_filter(['metadata', 'metrics', 'topic_count', 'topic_name_schemes', 'word_constraints']),
    'topic_attr': get_list_filter(['metadata', 'metrics', 'names', 'pairwise', 'top_n_words', 'top_n_documents', 'word_tokens', 'word_token_documents_and_locations']),
    'document_attr': get_list_filter(['text', 'metadata', 'metrics', 'top_n_topics', 'top_n_words', 'kwic', 'word_token_topics_and_locations', 'intro_snippet']),

    # extra parameters
    'topic_pairwise': filter_csv_to_list,
    'top_n_documents': get_filter_int(low=0),
    'top_n_words': get_filter_int(low=1),
    
    'document_continue': get_filter_int(low=0),
    'document_seed': get_filter_int(),
    'document_limit': get_filter_int(low=1, high=MAX_DOCUMENTS_PER_REQUEST),
    'document_n_words': get_filter_int(low=1),
    
    'token_indices': filter_csv_to_list,
    
    # TODO move this to an encrypted connection
    'word_constraints': filter_to_json,
}

TERMS = """\
THE WEBSITE IS PROVIDED AS A PUBLIC SERVICE IN THE HOPE THAT IT WILL BE USEFUL, BUT WITHOUT ANY WARRANTY. IT IS PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND, EITHER EXPRESSED OR IMPLIED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE. THE ENTIRE RISK AS TO THE QUALITY AND PERFORMANCE OF THE WEBSITE IS WITH YOU. YOUR USE OF ANY INFORMATION OR MATERIALS ON THIS WEBSITE IS ENTIRELY AT YOUR OWN RISK, FOR WHICH WE SHALL NOT BE LIABLE. IT SHALL BE YOUR OWN RESPONSIBILITY TO ENSURE THAT ANY PRODUCTS, SERVICES OR INFORMATION AVAILABLE THROUGH THIS WEBSITE MEET YOUR SPECIFIC REQUIREMENTS.

IN NO EVENT UNLESS REQUIRED BY APPLICABLE LAW THE AUTHORS WILL BE LIABLE TO YOU FOR DAMAGES, INCLUDING ANY GENERAL, SPECIAL, INCIDENTAL OR CONSEQUENTIAL DAMAGES ARISING OUT OF THE USE OR INABILITY TO USE THE WEBSITE (INCLUDING BUT NOT LIMITED TO LOSS OF DATA OR DATA BEING RENDERED INACCURATE OR LOSSES SUSTAINED BY YOU OR THIRD PARTIES OR A FAILURE OF THE WEBSITE TO OPERATE WITH ANY OTHER PROGRAMS OR WEBSITES), EVEN IF THE AUTHORS HAVE BEEN ADVISED OF THE POSSIBILITY OF SUCH DAMAGES.

LIKE MOST WEBSITES, THE TOPICAL GUIDE COLLECTS NON-PERSONALLY-IDENTIFYING INFORMATION OF THE SORT THAT WEB BROWSERS AND SERVERS TYPICALLY MAKE AVAILABLE, SUCH AS THE BROWSER TYPE, LANGUAGE PREFERENCE, REFERRING SITE, AND THE DATE AND TIME OF EACH VISITOR REQUEST. OUR PURPOSE IN COLLECTING NON-PERSONALLY IDENTIFYING INFORMATION IS TO BETTER UNDERSTAND HOW THE TOPICAL GUIDE'S VISITORS USE ITS WEBSITE. WE RESERVE THE RIGHT TO PUBLISH ACADEMIC RESEARCH BASED ON THIS DATA, AND PUBLISH ANY COLLECTED, WITH THE EXCEPTION OF ANY PERSONALLY-IDENTIFYING INFORMATION.

THE TOPICAL GUIDE ALSO COLLECTS POTENTIALLY PERSONALLY-IDENTIFYING INFORMATION LIKE INTERNET PROTOCOL (IP) ADDRESSES FOR LOGGED IN USERS. HOWEVER, WE WILL NOT UNIQUE IP ADDRESSES.

ANY ACTIVITIES USING THE WEBSITE OR OUR SERVICE INCLUDING BUT NOT LIMITED TO ILLEGAL ACTIVITIES, DENIAL OF SERVICE, INTERNET SPAM, MANIPULATION OF SEARCH ENGINE RANKINGS ARE PROHIBITED. THE ABSENCE OF AN ACTIVITY FROM THIS LIST OF PROHIBITIONS SHALL NOT BE CONSTRUED TO MEAN THAT SUCH MALICIOUS ACTIVITIES ARE PERMITTED.

WE RESERVE THE RIGHT TO MAKE CHANGES TO THESE TERMS FROM TIME TO TIME WITHOUT NOTIFICATION. IF YOU USE THE SERVICE AFTER THE TERMS HAVE CHANGED, WE WILL TREAT YOUR USE AS ACCEPTANCE OF THE UPDATED TERMS.
"""

def query_api(unfiltered_options):
    options = filter_request(unfiltered_options, OPTIONS_FILTERS)
    result = {}
    if 'server' in options:
        result['server'] = query_server(options)
    if 'datasets' in options:
        result['datasets'] = query_datasets(options)
    return result

def query_server(options):
    """Gather information about the server."""
    
    def get_version(x):
        try:
            tags = Repo('.').tags
            return unicode(tags[-1])
        except:
            return 'No version available.'
    
    def get_terms(x):
        file_name = os.path.join(os.path.abspath(os.path.dirname(os.path.dirname(__file__))), 'templates', 'terms.html')
        with io.open(__file__, 'r', encoding='utf-8') as f:
            return f.read()
    
    SERVER_ATTR = {
        'version': lambda x: get_version(x),
        'api_version': lambda x: 'v1',
        'max_documents_per_request': lambda x: MAX_DOCUMENTS_PER_REQUEST,
        'license_url': lambda x: 'http://www.gnu.org/licenses/agpl.html',
        'terms': lambda x: TERMS,
        'metadata_types': lambda x: dict(MetadataType.DATATYPE_CHOICES), 
        'metadata_meanings': lambda x: dict(MetadataType.MEANING_CHOICES),
    }
    
    server_attr = options.setdefault('server', [])
    
    server = {}
    if server_attr == '*':
        server_attr = SERVER_ATTR
    for attr in server_attr:
        server[attr] = SERVER_ATTR[attr](None)
    
    return server

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
        'document_metadata_ordinals': lambda dataset: dataset.get_document_metadata_ordinals(),
        'document_metadata_meanings': lambda dataset: dataset.get_document_metadata_meanings(),
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
        
        attributes['last_updated'] = unicode(dataset_db.last_updated)
        
        datasets[dataset_db.name] = attributes
        
    return datasets

# TODO move this to an encrypted connection
def modify_analysis(options, dataset_db, analysis_db):
	from import_tool.import_system_utilities import get_common_working_directories, resume_analysis, copy_analysis_directory
	from import_tool.analysis.interfaces.mallet_analysis import MalletLdaAnalysis
	from os.path import join
	result = {}
	
	if 'word_constraints' in options:
        counter = 2
		new_analysis_name = analysis_db.name + str(counter)
        while Analysis.objects.exists(name=new_analysis_name):
            counter += 1
            new_analysis_name = analysis_db.name + str(counter)
        word_constraints = options['word_constraints']
		print(word_constraints)
        
        # copy the working directory
        copy_analysis_directory(dataset_db.directory, analysis_db.name, new_analysis_name)
        
		# TODO make synchronous call to mallet itm
		directories = get_common_working_directories(dataset_db.name)
		mallet_itm_analysis = MalletItmAnalysis(join(directories['topical_guide'], 'tools/mallet_itm/mallet'), directories['dataset'], directories['base'])
        mallet_itm_analysis.name = new_analysis_name
        mallet_itm_analysis.set_constraints(word_constraints['merge'], word_constraints['split'])
		resume_analysis('default', dataset_db.name, mallet_itm_analysis, directories, verbose=True)
		result['new_analysis_name'] = new_analysis_name
	
	return result

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
        'topic_name_schemes': lambda analysis_db: analysis_db.get_topic_name_schemes(),
        'word_constraints': lambda analysis_db: analysis_db.get_word_constraints(),
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
        
        attributes['last_updated'] = unicode(analysis_db.last_updated)
        
        analyses[analysis_db.name] = attributes
        
        if 'word_constraints' in options:
            modify_analysis(options, dataset_db, analysis_db)
    
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
                if 'metadata_name' in options:
                    
                    metadata_name = options['metadata_name']
                    metadata_type_query = DocumentMetadataValue.objects.values_list('metadata_type__datatype').filter(document__dataset=dataset_db, metadata_type__name=metadata_name).distinct()
                    metadata_type = metadata_type_query[0][0]
                    if 'metadata_value' in options:
                        attributes['words'] = topic_db.top_n_words(options['words'], \
                            top_n=options['top_n_words'], \
                            metadata_name=metadata_name, \
                            metadata_type=metadata_type, \
                            metadata_value=options['metadata_value'] )
                    elif 'metadata_range' in options:
                        attributes['words'] = topic_db.top_n_words(options['words'], \
                            top_n=options['top_n_words'], \
                            metadata_name=metadata_name, \
                            metadata_type=metadata_type, \
                            metadata_range=options['metadata_range'] )
                else:
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
        'intro_snippet': lambda doc: doc.get_intro_snippet() if dataset_db.public_documents else "Document snippet unavailable.",
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
    if options['documents'] == '*':
        doc_count = dataset_db.documents.count()
        if doc_count > limit: # Restrict the documents to a certain range
            if 'document_seed' in options:
                sample_indices = reservoir_sample(limit, doc_count, options['document_seed'])
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
                end_index = start + limit
                while i < end_index:
                    range_end = chunk_size + i
                    if range_end >= end_index:
                        range_end = end_index - 1
                    chain.append(documents_queryset.filter(index__range=[i, range_end]))
                    i += range_end - i + 1 # ranges include the end value
                documents_queryset = itertools.chain(*chain)
    else:
        doc_count = len(options['documents'])
        if doc_count > limit:
            raise Exception("Too many documents.")
    
    # Must come after range filtering since similar variables are used.
    if 'top_n_topics' in document_attr:
        query = analysis_db.tokens.values_list('document', 'topics__number').annotate(count=Count('document'))
        if options['documents'] == '*':
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
        else:
            query.filter(document__filename__in=options['documents'])
        
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
            attributes['metrics']['Length in Characters'] = document_db.length
        if 'top_n_topics' in options['document_attr']:
            if document_db.id in top_n_topics:
                attributes['topics'] = top_n_topics[document_db.id]
            else:
                attributes['topics'] = {}
        if 'top_n_words' in options['document_attr'] and 'words' in options and 'document_n_words' in options:
            attributes['top_n_words'] = document_db.get_top_n_words(options['words'], top_n=options['document_n_words'])
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

