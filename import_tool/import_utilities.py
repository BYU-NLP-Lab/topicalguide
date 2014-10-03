from __future__ import print_function

import os
import json
import random
import re
import codecs
import math

from topic_modeling import settings
from django.core.management import call_command
settings.DEBUG = False # Disable debugging to prevent the database layer from caching queries and thus hogging memory
# the 'DJANGO_SETTINGS_MODULE' must be set before the database can be used.
os.environ['DJANGO_SETTINGS_MODULE'] = 'topic_modeling.settings'
from django.db import transaction
from django.db.models import Max

import basic_tools
from dataset_scripts import database_import
from dataset_scripts import metadata
from analysis_scripts import analysis_import
from analysis_scripts import mallet
from helper_scripts.name_schemes.top_n import TopNTopicNamer
from metric_scripts import metric_import

from topic_modeling.visualize.models import *

TOKEN_REGEX = r"(([^\W])+([-',])?)+([^\W])+"
BASIC_METRICS = [
    'dataset_token_count', 'dataset_type_count',
    'document_token_count', 'document_type_count', 'document_topic_entropy', 
    'analysis_entropy',
    'topic_token_count', 'topic_type_count', 'topic_document_entropy', 'topic_word_entropy', 
    #~ 'document_pairwise_topic_correlation', # This is an expensive metric.
    'topic_pairwise_document_correlation', 'topic_pairwise_word_correlation',
]

def make_working_dir():
    """Make the 'working/' dir and return the absolute path."""
    topical_guide_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    working_dir = os.path.join(topical_guide_dir, 'working')
    if not os.path.exists(working_dir):
        os.makedirs(working_dir)
    return working_dir

def get_common_working_directories(dataset_identifier):
    """
    Create commonly used directory paths.
    Return a dictionary with 'topical_guide', 'working', 'dataset', and 'documents' that map to the correct directory.
    """
    topical_guide_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    working_dir = make_working_dir()
    dataset_dir = os.path.join(working_dir, 'datasets', dataset_identifier) # not the directory containing the source dataset information
    if not os.path.exists(dataset_dir):
        os.makedirs(dataset_dir)
    document_dir = os.path.join(dataset_dir, 'files') # TODO change this to documents
    if not os.path.exists(document_dir):
        os.makedirs(document_dir)
    directories = {
        'topical_guide': topical_guide_dir, 
        'working': working_dir, 
        'dataset': dataset_dir, 
        'documents': document_dir
    }
    return directories

def run_syncdb(database_info):
    """
    Make sure that the database tables are created.
    Return the identifier the import process should use.
    If database_info is None the default database will be used.
    """
    dataset_identifier = 'default'
    if database_info: # create an entry in DATABASES if database_info is present
        dataset_identifier = '12345'
        while dataset_identifier in settings.DATABASES:
            dataset_identifier = str(random.randint(1, 2000000))
        settings.DATABASES[dataset_identifier] = database_info
    call_command('syncdb', database=dataset_identifier)
    return dataset_identifier

def import_dataset(database_id, dataset, directories, 
                   token_regex=TOKEN_REGEX, 
                   stopwords=None, find_bigrams=False, keep_singletons=False):
    """Transfer document content and metadata to database.
    By default token_regex is set to recogize sequences of unicode alpha characters.
    Return unique dataset name as found in database.
    """
    dataset_dir = directories['dataset']
    document_dir = directories['documents']
    stopwords_file = os.path.join(dataset_dir, "stopwords.json")
    
    # Test database existence of dataset to prevent re-bigram finding, etc.
    if not Dataset.objects.using(database_id).filter(name=dataset.get_identifier()).exists():
        # Get stopwords list, if any, and add word types below the threshold to it.
        if not stopwords:
            stopwords = {}
        
        if not keep_singletons:
            word_type_count_threshold = max(1, int(math.log(len(dataset), 10)) - 2)
            temp_word_type_counts = {}
            for doc in dataset:
                for word_index, match in enumerate(re.finditer(token_regex, doc.get_content(), re.UNICODE)):
                    word_type = match.group().lower()
                    temp_word_type_counts[word_type] = temp_word_type_counts.setdefault(word_type, 0) + 1
            for word_type, count in temp_word_type_counts.iteritems(): # add singletons to stopword list
                if count <= word_type_count_threshold:
                    stopwords[word_type] = True
            temp_word_type_counts = None
        
        if 'united' in stopwords:
            raise Exception('united in stopwords')
        # Bigrams, iterate through documents and train.
        if find_bigrams:
            from simple_bigram_finder import SimpleBigramFinder
            bigram_finder = SimpleBigramFinder(stopwords=stopwords, token_regex=token_regex)
            def text_iterator():
                for doc in dataset:
                    yield doc.get_identifier(), doc.get_content()
            bigram_finder.train(text_iterator())
            bigram_finder.print_bigrams()
        
        # Copy documents.
        for doc in dataset:
            content = doc.get_content()
            if find_bigrams: # Apply bigrams.
                content = bigram_finder.combine_bigrams(content)
            full_path = os.path.join(document_dir, doc.get_identifier())
            with codecs.open(full_path, 'w', 'utf-8') as f:
                f.write(content)
        
        # Store stopwords.
        with codecs.open(stopwords_file, 'w', 'utf-8') as stop_f:
            stop_f.write(json.dumps(stopwords))
    
    # Once all copied documents are present in the documents folder we're done preprocessing.
    # Now the database import begins.
    # Create database entry for dataset.
    dataset_db = database_import.create_dataset_db_entry(database_id, 
                                                         dataset, 
                                                         dataset_dir, 
                                                         document_dir)

    # Import each document, tokens, types, and metadata into the database.
    with codecs.open(stopwords_file, 'r', 'utf-8') as stop_f:
        stopwords = json.loads(stop_f.read())
    # transfer all documents and collect document info
    doc_identifiers = {}
    all_words = {}
    all_doc_metadata = {}
    for doc in dataset:
        doc_id = doc.get_identifier()
        # get document full path
        full_path = os.path.join(document_dir, doc_id)
        doc_identifiers[doc_id] = full_path
        # get metadata
        all_doc_metadata[doc_id] = doc.get_metadata()
        # get words
        with codecs.open(full_path, 'r', 'utf-8') as f:
            content = f.read()
        words = []
        for word_index, match in enumerate(re.finditer(token_regex, content, re.UNICODE)):
            word = match.group().lower()
            if word not in stopwords:
                start = match.start()
                words.append((word, word_index, start))
        all_words[doc_id] = words
    
    # create entries for each document
    print('Importing documents into database...')
    database_import.import_documents_into_database(database_id, dataset.get_identifier(), doc_identifiers)
    
    # import each document's words into the database
    print('Importing document words into database...')
    database_import.import_document_word_tokens(database_id, dataset.get_identifier(), all_words)
    
    # write the dataset metadata to the database
    dataset_metadata = dataset.get_metadata()
    dataset_metadata_types = {}
    basic_tools.collect_types(dataset_metadata_types, dataset_metadata)
    print('Importing dataset metadata into database...')
    metadata.import_dataset_metadata_into_database(database_id, dataset_db, dataset_metadata, 
                                                   dataset_metadata_types)
    
    # write the document metadata to the database
    all_document_metadata_types = {}
    for key, value in all_doc_metadata.items():
        basic_tools.collect_types(all_document_metadata_types, value)
    print('Importing document metadata into database...')
    metadata.import_document_metadata_into_database(database_id, dataset_db, all_doc_metadata,
                                                    all_document_metadata_types)
    return dataset.get_identifier()

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

def run_analysis(database_id, dataset_name, analysis, directories):
    """Import the given analysis.  Return unique analysis name for dataset."""
    print('Running analysis...')
    stopwords = {}
    stopwords_file = os.path.join(directories['dataset'], 'stopwords.json')
    if os.path.exists(stopwords_file):
        with codecs.open(stopwords_file, 'r', 'utf-8') as stop_f:
            stopwords = json.loads(stop_f.read())
    analysis.add_stopwords(stopwords)
    analysis.set_python_token_regex(TOKEN_REGEX)
    
    def document_iterator(doc_dir):
        for root, dirs, file_names in os.walk(doc_dir):
            for file_name in file_names:
                path = os.path.join(root, file_name)
                content = ''
                with codecs.open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                yield (file_name, content)
        raise StopIteration
    analysis.run_analysis(document_iterator(directories['documents']))
    print('Importing analysis output into database...')
    analysis_import.import_analysis(database_id, dataset_name, analysis)
    print('Importing analysis metadata into database...')
    analysis_db = Analysis.objects.using(database_id).get(name=analysis.get_identifier(), dataset__name=dataset_name)
    analysis_metadata_types = {}
    basic_tools.collect_types(analysis_metadata_types, analysis.get_metadata())
    metadata.import_analysis_metadata_into_database(database_id, analysis_db, analysis.get_metadata(), analysis_metadata_types)
    print('Naming topics...')
    topic_namer = TopNTopicNamer(database_id, dataset_name, analysis.get_identifier(), 3)
    if not TopicNameScheme.objects.using(database_id).filter(analysis=analysis_db, name=topic_namer.get_identifier()).exists():
        topic_namer.name_all_topics()
    return analysis.get_identifier()

def get_all_metric_names():
    """Return a list of all metric names."""
    from metric_scripts import all_metrics
    return all_metrics.keys()

def run_basic_metrics(database_id, dataset_name, analysis_name):
    """Run all basic metrics on the given dataset's analysis."""
    run_metrics(database_id, dataset_name, analysis_name, BASIC_METRICS)

def run_metrics(database_id, dataset_name, analysis_name, metrics):
    """Run the metrics specified in the given list."""
    
    from metric_scripts import all_metrics
    for metric_name in metrics:
        if not metric_name in all_metrics:
            print('Metric "' + metric_name + '" doesn\'t exist.')
            continue
        
        print('Running metric "' + metric_name + '"...')
        if metric_name.startswith('document_pairwise_'):
            metric_import.run_document_pairwise_metric(database_id, dataset_name, analysis_name,
                                                        all_metrics[metric_name])
        elif metric_name.startswith('topic_pairwise_'):
            metric_import.run_topic_pairwise_metric(database_id, dataset_name, analysis_name,
                                                     all_metrics[metric_name])
        elif metric_name.startswith('dataset_'):
            metric_import.run_dataset_metric(database_id, dataset_name, analysis_name,
                                              all_metrics[metric_name])
        elif metric_name.startswith('document_'):
            metric_import.run_document_metric(database_id, dataset_name, analysis_name,
                                               all_metrics[metric_name])
        elif metric_name.startswith('analysis_'):
            metric_import.run_analysis_metric(database_id, dataset_name, analysis_name,
                                               all_metrics[metric_name])
        elif metric_name.startswith('topic_'):
            metric_import.run_topic_metric(database_id, dataset_name, analysis_name,
                                            all_metrics[metric_name])
        

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
