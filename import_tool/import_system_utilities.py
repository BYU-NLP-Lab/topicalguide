from __future__ import division, print_function, unicode_literals

import os
import json
import random
import re
import math
import time

import django
from topicalguide import settings
from topicalguide.settings import BASE_DIR, WORKING_DIR
from django.core.management import call_command
# Disable debugging to prevent the database layer from caching queries
#~ settings.DEBUG = False # TODO uncomment this
# the 'DJANGO_SETTINGS_MODULE' must be set before the database models can be used.
os.environ['DJANGO_SETTINGS_MODULE'] = 'topicalguide.settings'
from django.db import transaction, connections
from django.db.models import Max

import basic_tools
from tools import VerboseTimer
from dataset.utilities import create_dataset, create_documents
from analysis.utilities import get_all_word_types, create_analysis, \
     create_word_type_entries, create_tokens, create_topic_heirarchy, \
     create_stopwords, create_excluded_words, create_topic_names
from analysis.name_schemes.top_n import TopNTopicNamer
from analysis.name_schemes.tf_itf import TfitfTopicNamer
from metadata.utilities import get_all_metadata_types
from visualize.models import *

DATABASE_OPTIMIZE_DEBUG = False # settings.DEBUG

MAX_TOKEN_LENGTH = WordType._meta.get_field('word').max_length

TOKEN_REGEX = u"(([^\\W])+([-'\u2019,])?)+([^\\W])+"
BASIC_DATASET_METRICS = [
    'dataset:document_count',
]
BASIC_ANALYSIS_METRICS = [
    'document-analysis:token_count', 'document-analysis:type_count', 'document-analysis:topic_entropy',
    'analysis:token_count', 'analysis:type_count', 'analysis:stopword_count',
    'analysis:excluded_word_count', 'analysis:entropy',
    'topic:token_count', 'topic:type_count', 'topic:document_entropy', 'topic:word_entropy',
    'topic-pairwise:document_correlation', 'topic-pairwise:word_correlation'
]
DEFAULT_TOPIC_NAMERS = [
    TopNTopicNamer(3), TfitfTopicNamer(3)
]

def make_working_dir():
    """Make the 'working/' dir.
    Return the absolute path.
    """
    return settings.WORKING_DIR # working/ dir made in the settings module now

def get_common_working_directories(dataset_identifier):
    """Create commonly used directory paths.
    dataset_identifier -- the unique name of the dataset
    Return a dictionary with 'topical_guide', 'working', 'dataset', and 'documents' that map to the correct directory path.
    """
    dataset_dir = os.path.join(WORKING_DIR, 'datasets', dataset_identifier)
    if not os.path.exists(dataset_dir):
        os.makedirs(dataset_dir)
    document_dir = os.path.join(dataset_dir, 'documents')
    if not os.path.exists(document_dir):
        os.makedirs(document_dir)
    directories = {
        'topical_guide': BASE_DIR, 
        'working': WORKING_DIR, 
        'dataset': dataset_dir, 
        'documents': document_dir,
        'base': BASE_DIR, 
    }
    return directories

def run_syncdb(database_info):
    """Make sure that the database tables are created.
    database_info -- a dictionary specifying the database info as dictated by Django;
                     if None then the default database is used
    Return the identifier the import process should use.
    """
    django.setup()
    dataset_identifier = 'default'
    if database_info: # create an entry in DATABASES if database_info is present
        dataset_identifier = '12345'
        while dataset_identifier in settings.DATABASES:
            dataset_identifier = str(random.randint(1, 2000000))
        settings.DATABASES[dataset_identifier] = database_info
    call_command('migrate', database=dataset_identifier)
    return dataset_identifier

def check_dataset(dataset):
    """Check the dataset for blank documents and print what metadata you have.
    This is useful for debugging and making sure that your dataset can be read.
    Also, this will inform you of the types of your metadata and any errors there.
    """
    blank_documents = []
    blank_metadata = []
    dataset_metadata_types = {}
    doc_metadata_types = {}
    
    basic_tools.collect_types(dataset_metadata_types, dataset.metadata)
    
    for doc in dataset:
        content = doc.content
        meta = doc.metadata
        assert type(content) == unicode
        if content == '' or content == None: # collect blank documents
            blank_documents.append(doc.source)
        if meta == {} or meta == None: # collect blank metadata
            blank_metadata.append(doc.source)
        else: # collect metadata types
            basic_tools.collect_types(doc_metadata_types, meta)
    
    
    
    
    if blank_metadata:
        print('List of files with no metadata: ')
        for doc_path in blank_metadata:
            print(doc_path)
        print()
    
    if blank_documents:
        print('List of files with no content: ')
        for doc_path in blank_documents:
            print(doc_path)
        print()
    
    dataset_metadata_types = {}
    basic_tools.collect_types(dataset_metadata_types, dataset.metadata)
    
    print('Dataset readable name: ')
    print('"' + dataset.name + '"')
    print()
    
    if dataset_metadata_types:
        print('Listing of dataset metadata and their associated types: ')
        for key, value in dataset_metadata_types.items():
            print(key + ': ' + value)
    else:
        print('No dataset metadata.')
    print()
    for key, value in dataset.metadata_types.iteritems():
        if key not in dataset_metadata_types:
            print("Metadata type in dataset metadata_types not specified: " + unicode(key))
        else:
            if dataset_metadata_types[key] != value:
                print("Metadata type for dataset metadata_types doesn't match that found: %s: %s"%(unicode(key), unicode(value)))
    
    if doc_metadata_types:
        print('Listing of document metadata and their associated types: ')
        for key, value in doc_metadata_types.items():
            print(key + ': ' + value)
    else:
        print('No document metdata')
    for key, value in dataset.document_metadata_types.iteritems():
        if key not in doc_metadata_types:
            print("Metadata type in document metadata_types not specified: " + unicode(key))
        else:
            if doc_metadata_types[key] != value:
                print("Metadata type for document metadata_types doesn't match that found: %s: %s"%(unicode(key), unicode(value)))
    
    print()

def import_dataset(database_id, dataset, directories, **kwargs):
    """Transfer documents and import content into database.
    Positional arguments:
    database_id -- the dict key specifying the database in django
    dataset -- an AbstractDataset
    directories -- dict returned from get_common_working_directories
    
    Keyword arguments:
    public -- make the dataset public (default False)
    public_documents -- make the document text available (default False)
    verbose -- print output about progress (default False)
    
    Return the dataset's name/identifier.
    """
    verbose = kwargs.setdefault('verbose', False)
    
    if verbose: print('Importing dataset: '+dataset.name)
    
    dataset_dir = directories['dataset']
    
    if DATABASE_OPTIMIZE_DEBUG:
        con = connections[database_id]
        query_count = len(con.queries)
    
    meta_types_db = {}
    
    if verbose: print('Creating dataset entry.')
    dataset_db = create_dataset(database_id, dataset, dataset_dir, meta_types_db, **kwargs)
    
    if DATABASE_OPTIMIZE_DEBUG:
        print('Dataset and metadata query count:', len(con.queries) - query_count)
        query_count = len(con.queries)
    
    if verbose: print('Copying documents and creating document entries.')
    if not dataset_db.documents.exists():
        create_documents(database_id, dataset_db, dataset, meta_types_db, verbose)
    
    if DATABASE_OPTIMIZE_DEBUG:
        print('Documents and metadata query count:', len(con.queries) - query_count)
    
    dataset_db.visible = True
    dataset_db.save()
    
    if verbose: print('Running dataset metrics.')
    run_metrics(database_id, dataset_db.name, None, BASIC_DATASET_METRICS)
    
    if verbose: print('Done importing '+dataset.name+'.')
    
    return dataset.name

# TODO take the output of the function and store the document metadata values
# in the database
def run_document_metadata_generator(database_id, dataset_name, function):
    dataset_db = Dataset.objects.using(database_id).get(name=dataset_name)
    metadata_values = function(dataset_db, dataset_db.documents.all())

def check_analysis(database_id, dataset_name, analysis, directories, 
                 topic_namers=None, verbose=False):
    """The purpose of this is to test an analysis for basic errors
    such as incorrect token indices and start indices, inappropriate topic
    heirarchies, tokens that are too long, whether or not a token is a
    stopword, and whether or not a token is part of the vocabulary.  Any errors
    are posted to the console.
    """
    def dict_to_string(d):
        result = ''
        for k, v in d.iteritems():
            result += unicode(k) + ': ' + unicode(v) + '\n'
        return result
    
    print('Analysis Name:', analysis.name)
    print('Analysis Metadata:', dict_to_string(analysis.metadata))
    print('Analysis Metadata Types:', dict_to_string(analysis.metadata_types))
    
    print('Running Analysis...')
    document_iterator = Document.objects.using(database_id).filter(dataset__name=dataset_name).order_by('index')
    document_iterator.prefetch_related('dataset', 'metadata', 'metadata__metadata_type')
    analysis.run_analysis(document_iterator)
    
    word_types_db = get_all_word_types(database_id)
    
    new_word_types = {}
    new_word_type_count = 0
    existing_word_type_count = 0
    for word_type in analysis.get_vocab_iterator():
        if word_type in word_types_db:
            existing_word_type_count += 1
        else:
            new_word_type_count += 1
            new_word_types[word_type.lower()] = True
    print('New Word Types:', new_word_type_count)
    print('Existing Word Types:', existing_word_type_count)
    
    topics = {}
    curr_doc = -1
    curr_text = ''
    word_token_count = 0
    for document_index, start_index, token, token_abstraction, topic_number_list in analysis.get_token_iterator():
        try:
            if document_index != curr_doc:
                curr_doc = document_index
                curr_text = document_iterator[curr_doc].get_content()
            assert start_index >= 0 and start_index < len(curr_text)
            assert token.lower() == curr_text[start_index: start_index + len(token)].lower()
            assert token_abstraction != None
            assert token in word_types_db or token in new_word_types
            assert token_abstraction in word_types_db or token_abstraction in new_word_types
            assert len(token) < MAX_TOKEN_LENGTH, 'Max length of token strings is %d.'%(MAX_TOKEN_LENGTH)
            assert len(token_abstraction) < MAX_TOKEN_LENGTH, 'Max length of token abstraction strings is %d.'%(MAX_TOKEN_LENGTH)
            for topic_num in topic_number_list:
                if topic_num not in topics:
                    topics[topic_num] = True
                assert topic_num >= 0
                assert type(topic_num) == int
            word_token_count += 1
        except AssertionError:
            print(document_index, start_index, token, token_abstraction, topic_number_list, curr_text[start_index: start_index + len(token)])
            print(curr_text)
            raise
    print('Basic token check passes.')
    print('Number of Word Tokens:', word_token_count)
    print('Number of Topics:', len(topics))
    
    parent_children = {}
    for parent_num, child_num in analysis.get_hierarchy_iterator():
        assert parent_num in topics
        assert child_num in topics
        if parent_num not in parent_children:
            parent_children[parent_num] = {child_num: True}
        else:
            parent_children[parent_num][child_num] = True
        if child_num in parent_children:
            assert parent_num not in parent_children[child_num]
    print('Topic hierarchy checks out.')
    print('Topic hierarchy:', parent_children)
    
    print('Stopword Count:', len(analysis.stopwords))
    print('Excluded Count:', len(analysis.excluded_words))
    

def run_analysis(database_id, dataset_name, analysis, directories, 
                 topic_namers=None, verbose=False):
    """Give the analysis the text for the documents allowing the bulk of the
    work to be done by the analysis. Import the tokens, topic token 
    relationships, topics, etc., into the database.
    Positional Arguments:
    database_id -- the dict key specifying the database in django
    dataset_name -- the name that uniquely identifies which dataset this
                    analysis will be run on
    analysis -- an AbstractAnalysis object
    directories -- dict returned from get_common_working_directories
    
    Keyword Arguments:
    topic_namers -- a list of AbstractTopicNamers that take an Analysis Django database
                    object and create topic names according to a naming scheme
    verbose -- if True notifications of progress will be output to the console
    
    Return the unique analysis name for the given dataset.
    """
    if verbose: print('Running analysis:', analysis.name)
    document_iterator = Document.objects.using(database_id).filter(dataset__name=dataset_name).order_by('index')
    document_iterator.prefetch_related('dataset', 'metadata')
    analysis.run_analysis(document_iterator)
    
    dataset_db = Dataset.objects.using(database_id).get(name=dataset_name)
    # word types should be relatively sparse, so we load all of them into memory
    word_types_db = get_all_word_types(database_id)
    meta_types_db = get_all_metadata_types(database_id, dataset_db)
    
    if verbose: print('Creating analysis entry.')
    analysis_db = create_analysis(database_id, dataset_db, analysis, meta_types_db)
    
    if verbose: print('Creating word type entries.')
    create_word_type_entries(database_id, analysis.get_vocab_iterator(), word_types_db)
    
    if not analysis_db.tokens.exists():
        if verbose: print('Creating token entries.')
        create_tokens(database_id, analysis_db, word_types_db, analysis.get_token_iterator(), verbose=verbose)
    
    if verbose: print('Adjusting topic heirarchy.')
    create_topic_heirarchy(database_id, analysis_db, analysis.get_hierarchy_iterator())
    
    if not analysis_db.stopwords.exists():
        if verbose: print('Creating stopword entries.')
        create_stopwords(database_id, analysis_db, word_types_db, analysis.stopwords)
    
    if not analysis_db.excluded_words.exists():
        if verbose: print('Creating excluded word entries.')
        create_excluded_words(database_id, analysis_db, word_types_db, analysis.excluded_words)
    
    if verbose: print('Naming topics.')
    
    if DATABASE_OPTIMIZE_DEBUG:
        con = connections[database_id]
        query_count = len(con.queries)
    
    if topic_namers == None:
        topic_namers = DEFAULT_TOPIC_NAMERS
    create_topic_names(database_id, analysis_db, topic_namers, verbose=verbose)
    
    if DATABASE_OPTIMIZE_DEBUG:
        total_queries = len(con.queries) - query_count
        print("Namers used %d queries."%(total_queries,))
        if total_queries > 10:
            for query in con.queries[query_count:]:
                print(query['time'])
                print(query['sql'])
    
    if verbose: print('Running metrics.')
    run_metrics(database_id, dataset_db.name, analysis_db.name, BASIC_ANALYSIS_METRICS)
    
    return analysis.name

# Warning! This code hasn't been updated.
# The purpose was to allow datasets to be imported into different
# databases.
def link_dataset(database_id, dataset_name):
    """
    Link the dataset, if it exists, to the default database.
    The database and tables must exist, that is, database_config must contain 
    valid configurations.
    If database_config is None, nothing happens.
    """
    # return if there is no linking to be done
    if database_id == 'default' or database_id is None or not database_id in settings.DATABASES:
        return
    
    # check that the dataset doesn't already exists in the default database
    if Dataset.objects.using('default').filter(name=dataset_name).exists() or \
        ExternalDataset.objects.using('default').filter(name=dataset_name).exists():
        print('Dataset name already exists in default database.')
        return
    
    # check that the given dataset exists
    if not Dataset.objects.using(database_id).filter(name=dataset_name).exists():
        print('Dataset does not exist in external database, nothing to link.')
        return
    
    database_config_text = json.dumps(settings.DATABASES[database_id])
    external_dataset = ExternalDataset.objects.create(name=dataset_name, database_settings=database_config_text)
    if external_dataset:
        print('Dataset linking successful.')
    else:
        print('Dataset linking failed.')

def get_all_metric_names():
    """Return a list of all metric names."""
    from metric import all_metrics
    return all_metrics.keys()

def run_metrics(database_id, dataset_name, analysis_name, metrics):
    """Run the metrics specified in the given list.
    database_id -- the dict key specifying the database in django
    dataset_name -- the name that uniquely identifies the dataset in question
    analysis_name -- the name that uniquely identifies the analysis in the
                     dataset; if None then all metrics must only be dataset
                     metrics
    metrics -- a list of metric names to be run
    """
    from metric import all_metrics, all_tables, all_metrics_exists
    from metric.utilities import get_metric_names, run_metric
    
    metrics_db = get_metric_names(database_id)
    dataset_db = Dataset.objects.using(database_id).get(name=dataset_name)
    if analysis_name is not None:
        analysis_db = Analysis.objects.using(database_id).get(dataset=dataset_db, name=analysis_name)
    else:
        analysis_db = None
    
    if DATABASE_OPTIMIZE_DEBUG:
        con = connections[database_id]
    
    for metric_name in metrics:
        if not metric_name in all_metrics:
            print('Metric "' + metric_name + '" does not exist.')
            continue
        if DATABASE_OPTIMIZE_DEBUG:
            query_count = len(con.queries)
        run_metric(database_id, dataset_db, analysis_db, metrics_db, all_tables[metric_name], all_metrics[metric_name], all_metrics_exists[metric_name])
        if DATABASE_OPTIMIZE_DEBUG:
            print("%s made %d queries."%(metric_name, len(con.queries) - query_count))
            #~ if (len(con.queries) - query_count) > 10:
                #~ for query in con.queries[query_count:query_count+3]:
                    #~ print(query)

# Warning! This code hasn't been updated.
# The purpose was to remove metrics from a dataset/analysis.
def remove_metrics(database_id, dataset_name, analysis_name, metrics=None):
    """Remove the listed metrics from the given dataset.  If metrics is None or empty, then remove all basic metrics."""
    from metric_scripts import all_metrics
    if metrics == None or metrics == []:
        metrics = BASIC_METRICS
    
    for metric_name in metrics:
        if not metric_name in all_metrics:
            print('Metric "' + metric_name + '" doesn\'t exist.')
            continue
        
        print('Removing metric "' + metric_name + '"...')
        if metric_name.startswith('document_pairwise_'):
            metric_import.remove_document_pairwise_metric(database_id, dataset_name, analysis_name,
                                                          all_metrics[metric_name])
        elif metric_name.startswith('topic_pairwise_'):
            metric_import.remove_topic_pairwise_metric(database_id, dataset_name, analysis_name,
                                                       all_metrics[metric_name])
        elif metric_name.startswith('dataset_'):
            metric_import.remove_dataset_metric(database_id, dataset_name, analysis_name,
                                                all_metrics[metric_name])
        elif metric_name.startswith('document_'):
            metric_import.remove_document_metric(database_id, dataset_name, analysis_name,
                                                 all_metrics[metric_name])
        elif metric_name.startswith('analysis_'):
            metric_import.remove_analysis_metric(database_id, dataset_name, analysis_name,
                                                 all_metrics[metric_name])
        elif metric_name.startswith('topic_'):
            metric_import.remove_topic_metric(database_id, dataset_name, analysis_name,
                                              all_metrics[metric_name])
    

# Warning! This code hasn't been updated.
# The purpose was to allow datasets to be migrated, or moved from one database to another.
def migrate_dataset(dataset_id, from_db_id, to_db_id):
    """
    Move a dataset from one database to another.
    Note that dataset_id is the unique name the dataset was given; also, 
    from_db_id and to_db_id are keys indicating which databases to use.
    It is assumed that the databases exists and have all of the necessary tables.
    Return nothing.
    """
    if not Dataset.objects.using(from_db_id).filter(name=dataset_id).exists():
        print('Dataset %s doesn\'t exist in the given database.' % (dataset_id))
        return
    
    # transfer dataset entry
    print('Creating dataset entry...')
    with transaction.atomic(using=to_db_id):
        if not Dataset.objects.using(to_db_id).filter(name=dataset_id).exists():
            dataset = Dataset.objects.using(from_db_id).get(name=dataset_id)
            dataset.id = None
            dataset.visible = False
            dataset.save(using=to_db_id)
    
    # get Dataset object for use elsewhere
    to_dataset = Dataset.objects.using(to_db_id).get(name=dataset_id)
    
    # transfer dataset metadata
    print('Migrating dataset metadata...')
    with transaction.atomic(using=to_db_id):
        if DatasetMetaInfoValue.objects.using(from_db_id).filter(dataset__name=dataset_id).count() != \
           DatasetMetaInfoValue.objects.using(to_db_id).filter(dataset__name=dataset_id).count():
            # create DatasetMetaInfo and key mappings
            meta_info_map = {}
            dataset_metadata_info = DatasetMetaInfo.objects.using(from_db_id).all()
            for dataset_metadata_type in dataset_metadata_info:
                meta_info, _ = DatasetMetaInfo.objects.using(to_db_id).get_or_create(name=dataset_metadata_type.name)
                meta_info_map[dataset_metadata_type.id] = meta_info.id
            
            # get largest primary key
            meta_info_value_id = get_max_pk(DatasetMetaInfoValue, to_db_id) + 1
            
            all_values = []
            from_meta_values = DatasetMetaInfoValue.objects.using(from_db_id).filter(dataset__id=to_dataset.id)
            for from_meta_value in from_meta_values:
                # collect values
                from_meta_value.id = meta_info_value_id
                meta_info_value_id += 1
                from_meta_value.dataset_id = dataset.id
                from_meta_value.info_type_id = meta_info_map[from_meta_value.info_type_id]
                all_values.append(from_meta_value)
            # commit values
            DatasetMetaInfoValue.objects.using(to_db_id).bulk_create(all_values)
    
    # get keys for general use later on
    from_dataset_pk = Dataset.objects.using(from_db_id).get(name=dataset_id).id
    to_dataset_pk = to_dataset.id
    
    # transfer dataset metrics
    # NOTE: The amount of data is minimal and thus this is not optimized.
    print('Migrating dataset metrics...')
    with transaction.atomic(using=to_db_id):
        if not DatasetMetricValue.objects.using(to_db_id).filter(dataset_id=to_dataset_pk).exists():
            metric_values = DatasetMetricValue.objects.using(from_db_id).filter(dataset_id=from_dataset_pk)
            for value in metric_values:
                value.id = None
                value.dataset_id = to_dataset.id
                metric, _ = DatasetMetric.objects.using(to_db_id).get_or_create(name=value.metric.name)
                value.metric_id = metric.id
                value.save(using=to_db_id)
    
    # transfer documents
    # TODO change full_path info
    print('Migrating documents...')
    with transaction.atomic(using=to_db_id):
        if Document.objects.using(from_db_id).filter(dataset__name=dataset_id).count() != \
           Document.objects.using(to_db_id).filter(dataset__name=dataset_id).count():
            curr_doc_id = get_max_pk(Document, to_db_id) + 1
            documents = Document.objects.using(from_db_id).filter(dataset__name=dataset_id)
            docs_to_commit = []
            for document in documents:
                document.id = curr_doc_id
                curr_doc_id += 1
                document.dataset_id = dataset.id
                docs_to_commit.append(document)
            Document.objects.using(to_db_id).bulk_create(docs_to_commit)
    
    # generate key mappings for general use later on
    document_pk_map = {}
    from_documents = Document.objects.using(from_db_id).filter(dataset_id=from_dataset_pk)
    to_documents = Document.objects.using(to_db_id).filter(dataset_id=to_dataset_pk)
    to_documents.count()
    for doc in from_documents:
        document_pk_map[doc.id] = to_documents.get(filename=doc.filename).id
    
    # transfer document metadata
    print('Migrating document metadata...')
    with transaction.atomic(using=to_db_id):
        # get largest primary key
        
        from_meta_values = DocumentMetaInfoValue.objects.using(from_db_id).filter(document__dataset__name=dataset_id)
        if from_meta_values.count() != \
           DocumentMetaInfoValue.objects.using(to_db_id).filter(document__dataset__name=dataset_id).count():
            meta_info_value_id = get_max_pk(DocumentMetaInfoValue, to_db_id) + 1
            
            # create DocumentMetaInfo and key mappings
            meta_info_map = {}
            document_metadata_info = DocumentMetaInfo.objects.using(from_db_id).filter(values__document__dataset__name=dataset_id)
            for document_metadata_type in document_metadata_info:
                meta_info, _ = DocumentMetaInfo.objects.using(to_db_id).get_or_create(name=document_metadata_type.name)
                meta_info_map[document_metadata_type.id] = meta_info.id
            
            # get all values and commit them
            all_values = []
            for value in from_meta_values:
                value.id = meta_info_value_id
                meta_info_value_id += 1
                value.document_id = document_pk_map[value.document_id]
                value.info_type_id = meta_info_map[value.info_type_id]
                all_values.append(value)
            DocumentMetaInfoValue.objects.using(to_db_id).bulk_create(all_values)
    
    # transfer analyses
    print('Migrating analyses...')
    # note that analyses is the plural form of analysis
    with transaction.atomic(using=to_db_id):
        if not Analysis.objects.using(to_db_id).filter(dataset__name=dataset_id).exists():
            from_analyses = Analysis.objects.using(from_db_id).filter(dataset_id=from_dataset_pk)
            for analysis in from_analyses:
                analysis.id = None
                analysis.dataset_id = to_dataset_pk
                analysis.save(using=to_db_id)
    
    # generate key mappings for general use later on
    analysis_pk_map = {}
    from_analyses = Analysis.objects.using(from_db_id).filter(dataset_id=from_dataset_pk)
    to_analyses = Analysis.objects.using(to_db_id).filter(dataset_id=to_dataset_pk)
    for analysis in from_analyses:
        analysis_pk_map[analysis.id] = to_analyses.get(name=analysis.name).id
    
    # transfer analyses metrics
    print('Migrating analyses metrics...')
    with transaction.atomic(using=to_db_id):
        for analysis in from_analyses:
            if not AnalysisMetricValue.objects.using(to_db_id).filter(analysis_id=analysis_pk_map[analysis.id]).exists():
                metric_values = AnalysisMetricValue.objects.using(from_db_id).filter(analysis_id=analysis.id)
                for value in metric_values:
                    metric, _ = AnalysisMetric.objects.using(to_db_id).get_or_create(name=value.metric.name)
                    value.id = None
                    value.analysis_id = analysis_pk_map[analysis.id]
                    value.metric_id = metric.id
                    value.save(using=to_db_id)
    
    # transfer topics, topic names, and topic name schemes
    print('Migrating topics, topic names, and topic name schemes...')
    with transaction.atomic(using=to_db_id):
        to_topic_name_schemes = TopicNameScheme.objects.using(to_db_id).all()
        for analysis in from_analyses:
            if not Topic.objects.using(to_db_id).filter(analysis_id=analysis_pk_map[analysis.id]).exists():
                topics = Topic.objects.using(from_db_id).filter(analysis_id=analysis.id)
                for topic in topics:
                    topic_names = TopicName.objects.using(from_db_id).filter(topic_id=topic.id)
                    topic.id = None
                    topic.analysis_id = analysis_pk_map[analysis.id]
                    topic.save(using=to_db_id)
                    for name in topic_names:
                        name.id = None
                        name.topic_id = topic.id
                        name_scheme, _ = to_topic_name_schemes.get_or_create(name=name.name_scheme.name, analysis_id=analysis.id)
                        name.name_scheme_id = name_scheme.id
                        name.save(using=to_db_id)
    
    # generate key mappings for general use later on
    topic_pk_map = {}
    from_topics = Topic.objects.using(from_db_id).filter(analysis__dataset_id=from_dataset_pk)
    to_topics = Topic.objects.using(to_db_id).filter(analysis__dataset_id=to_dataset_pk)
    to_topics.count()
    for topic in from_topics:
        topic_pk_map[topic.id] = to_topics.get(number=topic.number, analysis_id=analysis_pk_map[topic.analysis_id]).id
    
    # transfer document metrics
    print('Migrating document metrics...')
    with transaction.atomic(using=to_db_id):
        for document in from_documents:
            if not DocumentMetricValue.objects.using(to_db_id).filter(document_id=document_pk_map[document.id]).exists():
                metric_values = DocumentMetricValue.objects.using(from_db_id).filter(document_id=document.id)
                for value in metric_values:
                    metric, _ = DocumentMetric.objects.using(to_db_id).get_or_create(name=value.metric.name, analysis_id=analysis_pk_map[value.metric.analysis_id])
                    value.id = None
                    value.metric_id = metric.id
                    value.document_id = document_pk_map[document.id]
                    value.save(using=to_db_id)
    
    # transfer topic metrics
    print('Migrating topic metrics...')
    with transaction.atomic(using=to_db_id):
        for topic in from_topics:
            if not TopicMetricValue.objects.using(to_db_id).filter(topic_id=topic_pk_map[topic.id]).exists():
                metric_values = TopicMetricValue.objects.using(from_db_id).filter(topic_id=topic.id)
                for value in metric_values:
                    metric, _ = TopicMetric.objects.using(to_db_id).get_or_create(name=value.metric.name, analysis_id=analysis_pk_map[value.metric.analysis_id])
                    value.id = None
                    value.topic_id = topic_pk_map[topic.id]
                    value.metric_id = metric.id
                    value.save(using=to_db_id)
    
    # transfer word tokens, word types, and word token to topics relations
    print('Migrating word tokens, word types, and word token to topics relations...')
    with transaction.atomic(using=to_db_id):
        if not WordToken.objects.using(to_db_id).filter(document__dataset__name=dataset_id).exists():
            word_type_pk = get_max_pk(WordType, to_db_id) + 1
            word_token_pk = get_max_pk(WordToken, to_db_id) + 1
            word_token_topic_pk = get_max_pk(WordToken_Topics, to_db_id) + 1
            
            # get all word types currently in the database
            to_word_types = dict((wtype.type, wtype) for wtype in WordType.objects.using(to_db_id).all())
            
            word_tokens = WordToken.objects.using(from_db_id).filter(document__dataset__name=dataset_id).select_related()
            #~ word_tokens.select_related()
            all_word_tokens = []
            all_word_types = []
            all_word_token_topics = []
            for token in word_tokens:
                # go over relations
                for topic in token.topics.all():#topic_relations:
                    word_token_topic = WordToken_Topics(wordtoken_id=word_token_pk, topic_id=topic_pk_map[topic.id])
                    word_token_topic.id = word_token_topic_pk
                    word_token_topic_pk += 1
                    all_word_token_topics.append(word_token_topic)
                
                word = token.type.type
                # create WordType if word doesn't exist
                if not word in to_word_types:
                    word_type = WordType(id=word_type_pk, type=word)
                    word_type_pk += 1
                    to_word_types[word] = word_type
                    all_word_types.append(word_type)
                else:
                    word_type = to_word_types[word]
                token.id = word_token_pk
                word_token_pk += 1
                token.document_id = document_pk_map[token.document_id]
                token.type_id = word_type.id
                all_word_tokens.append(token)
                
                if len(all_word_tokens) > 100000:
                    WordType.objects.using(to_db_id).bulk_create(all_word_types)
                    WordToken.objects.using(to_db_id).bulk_create(all_word_tokens)
                    WordToken_Topics.objects.using(to_db_id).bulk_create(all_word_token_topics)
                    all_word_types = []
                    all_word_tokens = []
                    all_word_token_topics = []
            WordType.objects.using(to_db_id).bulk_create(all_word_types)
            WordToken.objects.using(to_db_id).bulk_create(all_word_tokens)
            WordToken_Topics.objects.using(to_db_id).bulk_create(all_word_token_topics)
    
    # transfer pairwise document metric values
    print('Migrating pairwise document metric values...')
    with transaction.atomic(using=to_db_id):
        # used to map document id's in the from database to those in the to database
        from_pairwise_document_metric = PairwiseDocumentMetric.objects.using(from_db_id).all()
        to_pairwise_document_metric = PairwiseDocumentMetric.objects.using(to_db_id).all()
        metric_pk_map = None
        
        values_to_commit = []
        for analysis in from_analyses:
            if not PairwiseDocumentMetricValue.objects.using(to_db_id).filter(metric__analysis_id=analysis_pk_map[analysis.id]).exists():
                if metric_pk_map == None:
                    metric_pk_map = {}
                    from_pairwise_document_metric.count()
                    to_pairwise_document_metric.count()
                    for metric in from_pairwise_document_metric:
                        if metric.analysis_id in analysis_pk_map:
                            m, _ = to_pairwise_document_metric.get_or_create(name=metric.name, analysis_id=analysis_pk_map[analysis.id])
                            metric_pk_map[metric.id] = m.id
                
                metric_values = PairwiseDocumentMetricValue.objects.using(from_db_id).filter(metric__analysis_id=analysis.id)
                
                for value in metric_values:
                    value.id = None
                    value.document1_id = document_pk_map[value.document1_id]
                    value.document2_id = document_pk_map[value.document2_id]
                    value.metric_id = metric_pk_map[value.metric_id]
                    values_to_commit.append(value)
        PairwiseDocumentMetricValue.objects.using(to_db_id).bulk_create(values_to_commit)
    
    # transfer pairwise topic metric values
    print('Migrating pairwise topic metric values...')
    with transaction.atomic(using=to_db_id):
        from_pairwise_document_metric = PairwiseTopicMetric.objects.using(from_db_id).all()
        to_pairwise_document_metric = PairwiseTopicMetric.objects.using(to_db_id).all()
        metric_pk_map = None
        
        values_to_commit = []
        for analysis in from_analyses:
            if not PairwiseTopicMetricValue.objects.using(to_db_id).filter(metric__analysis_id=analysis_pk_map[analysis.id]).exists():
                if metric_pk_map == None:
                    metric_pk_map = {}
                    for metric in from_pairwise_document_metric:
                        if metric.analysis_id in analysis_pk_map:
                            m, _ = to_pairwise_document_metric.get_or_create(name=metric.name, analysis_id=analysis_pk_map[metric.analysis_id])
                            metric_pk_map[metric.id] = m.id
                
                metric_values = PairwiseTopicMetricValue.objects.using(from_db_id).filter(metric__analysis_id=analysis.id)
                for value in metric_values:
                    value.id = None
                    value.topic1_id = topic_pk_map[value.topic1_id]
                    value.topic2_id = topic_pk_map[value.topic2_id]
                    value.metric_id = metric_pk_map[value.metric_id]
                    values_to_commit.append(value)
        PairwiseTopicMetricValue.objects.using(to_db_id).bulk_create(values_to_commit)
    
    # make the dataset visible
    to_dataset.visible = True
    to_dataset.save(using=to_db_id)
    
    print('Done')

# migrate helper function
def get_max_pk(django_model, database_id):
    """
    The django_model must have a non-auto-incrementing integer field named 'id'.
    Return the max id for the given model.
    """
    max_id = 0
    if django_model.objects.using(database_id).exists():
        max_id = django_model.objects.using(database_id).aggregate(Max('id'))['id__max']
    return max_id







# vim: et sw=4 sts=4
