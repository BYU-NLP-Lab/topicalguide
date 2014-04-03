from __future__ import print_function

import os
import json
import random
import re
import codecs

from topic_modeling import settings
from django.core.management import call_command
settings.DEBUG = False # Disable debugging to prevent the database layer from caching queries and thus hogging memory
# the 'DJANGO_SETTINGS_MODULE' must be set before the database can be used.
os.environ['DJANGO_SETTINGS_MODULE'] = 'topic_modeling.settings'
from django.db import transaction
from django.db.models import Max

from import_scripts import database_import
from import_scripts import metadata
from analysis_scripts import analysis_import
from analysis_scripts import mallet
from helper_scripts.name_schemes.top_n import TopNTopicNamer
from metric_scripts import import_metrics

from dataset_classes.generic_dataset import (GenericDataset, GenericDocument, GenericSubdocument)
from dataset_classes.generic_tools import GenericTools

#~ from topic_modeling.visualize.models import (Dataset, Analysis, TopicNameScheme, ExternalDataset)
from topic_modeling.visualize.models import *

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
    Return a dictionary with 'working', 'dataset', and 'documents' that map to the correct directory.
    """
    topical_guide_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    working_dir = make_working_dir()
    dataset_dir = os.path.join(working_dir, 'datasets', dataset_identifier) # not the directory containing the source dataset information
    if not os.path.exists(dataset_dir):
        os.makedirs(dataset_dir)
    document_dir = os.path.join(dataset_dir, 'files')
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

def import_dataset(database_id, dataset, dataset_dir, document_dir):
    """Transfer document content and metadata to database."""
    # create database entry for dataset
    dataset_db = database_import.create_dataset_db_entry(database_id, 
                                                         dataset, 
                                                         dataset_dir, 
                                                         document_dir)
    
    # transfer all documents and collect document info
    args = {'doc_identifiers': {}, 
            'words': {}, 
            'doc_metadata': {}, 
            'doc_dir': document_dir,
            'token_regex': ur'[a-zA-Z]+'}
    def document_info_collector(args, doc):
        """
        Function to aid in collecting data from documents. The data collected \
        includes metadata and words (including their location in the text).
        In addition to collecting data, the content is copied to a location \
        on the server.
        args should be a dict containing 'doc_metadata' and 'words'
        'doc_identifiers' a dictionary where the doc_identifier maps to its full path or uri
        'doc_metadata' should map to a dictionary with the doc_identifier mapping to its metadata
        'words' maps to a dictionary with doc_identifier mapping to a list of tuples
        'token_regex' is the regular expression used to identify words
        'doc_dir' should the the directory the document's content will be copied to
        """
        doc_id = doc.get_identifier()
        # get document full path
        full_path = os.path.join(args['doc_dir'], doc_id)
        args['doc_identifiers'][doc_id] = full_path
        # get metadata
        args['doc_metadata'][doc_id] = doc.get_metadata()
        # get words
        content = unicode(doc.get_content(), errors='ignore')
        args['words'][doc_id] = []
        words = args['words'][doc_id]
        for word_index, match in enumerate(re.finditer(args['token_regex'], content)):
            word = match.group().lower()
            start = match.start()
            words.append((word, word_index, start))
        # copy content to new location
        if not os.path.exists(full_path):
            with codecs.open(full_path, 'w', 'utf-8') as f:
                f.write(content)
    GenericTools.walk_documents(dataset, document_info_collector, args)
    
    # create entries for each document
    database_import.import_documents_into_database(database_id, dataset.get_identifier(), args['doc_identifiers'])
    
    # import each document's words into the database
    database_import.import_document_word_tokens(database_id, dataset.get_identifier(), args['words'])
    
    # write the dataset metadata to the database
    dataset_metadata = dataset.get_metadata()
    dataset_metadata_types = {}
    GenericTools.collect_types(dataset_metadata_types, dataset_metadata)
    print('Importing dataset metadata into database...')
    metadata.import_dataset_metadata_into_database(database_id, dataset_db, dataset_metadata, 
                                                   dataset_metadata_types)
                                          
    # write the document metadata to the database
    all_doc_metadata = args['doc_metadata']
    all_document_metadata_types = {}
    for key, value in all_doc_metadata.items():
        GenericTools.collect_types(all_document_metadata_types, value)
    print('Importing document metadata into database...')
    metadata.import_document_metadata_into_database(database_id, dataset_db, all_doc_metadata,
                                                    all_document_metadata_types)

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

def run_analysis(database_id, dataset, analysis_settings, topical_guide_dir, dataset_dir, document_dir):
    """
    Import the analysis by creating a DataSet object, Analysis DB object,
    a Metadata dictionary, and parse the mallet_output file.
    """
    print('Running analysis...')
    # run mallet
    print('  Preparing mallet input file...')
    mallet.prepare_mallet_input(dataset_dir, document_dir)
    print('  Running mallet...')
    mallet.run_mallet(analysis_settings, dataset_dir, document_dir, topical_guide_dir)
    # import the mallet output
    print('  Importing mallet output into database...')
    c = analysis_settings.get_mallet_configurations(topical_guide_dir, dataset_dir)
    analysis_import.import_analysis(database_id,
                                    dataset.get_identifier(), 
                                    analysis_settings.get_analysis_name(), 
                                    analysis_settings.get_analysis_readable_name(), 
                                    analysis_settings.get_analysis_description(), 
                                    c['mallet_output'], 
                                    c['mallet_input'], 
                                    r'[A-Za-z]+',
                                    analysis_settings.get_number_of_topics())
    # name the topics
    print('  Naming topics...')
    analysis_db = Analysis.objects.using(database_id).get(name=analysis_settings.get_analysis_name(), 
                                         dataset__name=dataset.get_identifier())
    topic_namer = TopNTopicNamer(database_id, dataset.get_identifier(), 
                                 analysis_settings.get_analysis_name(), 3)
    if not TopicNameScheme.objects.using(database_id).filter(analysis=analysis_db, name=topic_namer.get_identifier()).exists():
        topic_namer.name_all_topics()

def run_basic_metrics(database_id, dataset, analysis_settings):
    """Run all basic metrics; an analysis is required for this process."""
    print('Creating metrics...')
    dataset_name = dataset.get_identifier()
    analysis_name = analysis_settings.get_analysis_name()
    analysis_db = Analysis.objects.using(database_id).get(name=analysis_name, 
                                                          dataset__name=dataset_name)
    print('  Dataset metrics...')
    import_metrics.dataset_metrics(database_id, dataset_name, analysis_name) # depends on import_dataset_into_database()
    print('  Analysis metrics...')
    import_metrics.analysis_metrics(database_id, dataset_name, analysis_name, analysis_db)
    print('  Topic metrics...')
    import_metrics.topic_metrics(database_id, analysis_settings.get_topic_metrics(), dataset_name, analysis_name, analysis_db, analysis_settings.get_topic_metric_args())
    print('  Pairwise topic metrics...')
    import_metrics.pairwise_topic_metrics(database_id, analysis_settings.get_pairwise_topic_metrics(), dataset_name, analysis_name, analysis_db)
    print('  Document metrics...')
    import_metrics.document_metrics(database_id, dataset_name, analysis_name, analysis_db)
    print('  Pairwise document metrics...')
    import_metrics.pairwise_document_metrics(database_id, analysis_settings.get_pairwise_document_metrics(), dataset_name, analysis_name, analysis_db)

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
    with transaction.commit_on_success():
        if not Dataset.objects.using(to_db_id).filter(name=dataset_id).exists():
            dataset = Dataset.objects.using(from_db_id).get(name=dataset_id)
            dataset.id = None
            dataset.save(using=to_db_id)
    
    # transfer dataset metadata
    with transaction.commit_on_success():
        if DatasetMetaInfoValue.objects.using(from_db_id).filter(dataset__name=dataset_id).count() != \
           DatasetMetaInfoValue.objects.using(to_db_id).filter(dataset__name=dataset_id).count():
            dataset = Dataset.objects.using(to_db_id).get(name=dataset_id)
            # get largest primary key
            meta_info_value_id = 0
            if DatasetMetaInfoValue.objects.using(to_db_id).exists():
                meta_info_value_id = DatasetMetaInfoValue.objects.using(to_db_id).aggregate(Max('id'))['id__max'] + 1
            
            all_values = []
            dataset_metadata_info = DatasetMetaInfo.objects.using(from_db_id).all()
            for dataset_metadata_type in dataset_metadata_info:
                meta_info, _ = DatasetMetaInfo.objects.using(to_db_id).get_or_create(name=dataset_metadata_type.name)
                dataset_metadata_values = DatasetMetaInfoValue.objects.using(from_db_id).filter(info_type=dataset_metadata_type, dataset__name=dataset_id)
                # collect values
                for value in dataset_metadata_values:
                    value.id = meta_info_value_id
                    meta_info_value_id += 1
                    value.dataset_id = dataset.id
                    value.info_type_id = meta_info.id
                    all_values.append(value)
            # commit values
            DatasetMetaInfoValue.objects.using(to_db_id).bulk_create(all_values)
    
    # transfer dataset metrics
    with transaction.commit_on_success():
        dataset = Dataset.objects.using(to_db_id).get(name=dataset_id)
        if not DatasetMetricValue.objects.using(to_db_id).filter(dataset_id=dataset).exists():
            metric_values = DatasetMetricValue.objects.using(from_db_id).filter(dataset__name=dataset_id)
            for value in metric_values:
                value.id = None
                value.dataset_id = dataset.id
                metric, _ = DatasetMetric.objects.using(to_db_id).get_or_create(name=value.metric.name)
                value.metric_id = metric.id
                value.save(using=to_db_id)
    
    # transfer documents
    with transaction.commit_on_success():
        if Document.objects.using(from_db_id).filter(dataset__name=dataset_id).count() != \
           Document.objects.using(to_db_id).filter(dataset__name=dataset_id).count():
            dataset = Dataset.objects.using(to_db_id).get(name=dataset_id)
            documents = Document.objects.using(from_db_id).filter(dataset__name=dataset_id)
            for document in documents:
                document.id = None
                document.dataset_id = dataset.id
                document.save(using=to_db_id)
    
    # transfer document metadata
    with transaction.commit_on_success():
        # get largest primary key
        meta_info_value_id = 0
        if DocumentMetaInfoValue.objects.using(to_db_id).exists():
            meta_info_value_id = DocumentMetaInfoValue.objects.using(to_db_id).aggregate(Max('id'))['id__max'] + 1
        all_values = []
        # create query set for MetaInfo items
        all_meta_info = DocumentMetaInfo.objects.using(to_db_id).all()
        # iterate through documents
        documents = Document.objects.using(to_db_id).filter(dataset__name=dataset_id)
        for document in documents:
            # check if document metadata is present
            if DocumentMetaInfoValue.objects.using(from_db_id).filter(document__filename=document.filename).count() != \
               DocumentMetaInfoValue.objects.using(to_db_id).filter(document__filename=document.filename).count():
                # get all values for document
                document_metadata_values = DocumentMetaInfoValue.objects.using(from_db_id).filter(document__filename=document.filename)
                document_metadata_values.select_related()
                for value in document_metadata_values:
                    meta_info, _ = all_meta_info.get_or_create(name=value.info_type.name)
                    value.id = meta_info_value_id
                    meta_info_value_id += 1
                    value.document_id = document.id
                    value.info_type_id = meta_info.id
                    all_values.append(value)
        # commit all values
        DocumentMetaInfoValue.objects.using(to_db_id).bulk_create(all_values)
    
    # transfer document metrics
    with transaction.commit_on_success():
        documents = Document.objects.using(to_db_id).filter(dataset__name=dataset_id)
        for document in documents:
            if not DocumentMetricValue.objects.using(to_db_id).filter(document_id=document.id).exists():
                metric_values = DocumentMetricValue.objects.using(from_db_id).filter(document__filename=document.filename)
                for value in metric_values:
                    value.id = None
                    value.document_id = document.id
                    metric, _ = DocumentMetric.objects.using(to_db_id).get_or_create(name=value.metric.name)
                    value.metric_id = metric.id
                    value.save(using=to_db_id)
    
    # transfer words and word types
    with transaction.commit_on_success():
        word_type_pk = 0
        if WordType.objects.using(to_db_id).all().exists():
            word_type_pk = WordType.objects.using(to_db_id).all().aggregate(Max('id'))['id__max'] + 1
        word_token_pk = 0
        if WordToken.objects.using(to_db_id).all().exists():
            word_token_pk = WordToken.objects.using(to_db_id).all().aggregate(Max('id'))['id__max'] + 1
        
        # get all word types currently in the database
        word_types = dict((wtype.type, wtype) for wtype in WordType.objects.using(to_db_id).all())
        
        documents = Document.objects.using(to_db_id).filter(dataset__name=dataset_id)
        word_tokens_to_create = []
        word_types_to_create = []
        for document in documents:
            if not WordToken.objects.using(to_db_id).filter(document__filename=document.filename).exists():
                word_tokens = WordToken.objects.using(from_db_id).filter(document__filename=document.filename)
                word_tokens.select_related()
                for word_token in word_tokens:
                    word = word_token.type.type
                    if not word in word_types: # create a word type if it doesn't exist
                        word_type = WordType(id=word_type_pk, type=word)
                        word_types[word] = word_type
                        word_type_pk += 1
                        word_types_to_create.append(word_type)
                    else:
                        word_type = word_types[word]
                    word_token.id = word_token_pk
                    word_token_pk += 1
                    word_token.document_id = document.id
                    word_token.type_id = word_type.id
                    word_tokens_to_create.append(word_token)
                if len(word_tokens_to_create) > 100000:
                    WordType.objects.using(to_db_id).bulk_create(word_types_to_create)
                    WordToken.objects.using(to_db_id).bulk_create(word_tokens_to_create)
                    word_types_to_create = []
                    word_tokens_to_create = []
        WordType.objects.using(to_db_id).bulk_create(word_types_to_create)
        WordToken.objects.using(to_db_id).bulk_create(word_tokens_to_create)
    
    # transfer analyses
    # note that analyses is the plural form of analysis
    with transaction.commit_on_success():
        if not Analysis.objects.using(to_db_id).filter(dataset__name=dataset_id).exists():
            analyses = Analysis.objects.using(from_db_id).filter(dataset__name=dataset_id)
            dataset = Dataset.objects.using(to_db_id).get(name=dataset_id)
            for analysis in analyses:
                analysis.id = None
                analysis.dataset_id = dataset.id
                analysis.save(using=to_db_id)
    
    # transfer analyses metrics
    with transaction.commit_on_success():
        analyses = Analysis.objects.using(to_db_id).filter(dataset__name=dataset_id)
        for analysis in analyses:
            if not AnalysisMetricValue.objects.using(to_db_id).filter(analysis_id=analysis).exists():
                metric_values = AnalysisMetricValue.objects.using(from_db_id).filter(analysis__name=analysis.name)
                for value in metric_values:
                    metric, _ = AnalysisMetric.objects.using(to_db_id).get_or_create(name=value.metric.name)
                    value.id = None
                    value.analysis_id = analysis.id
                    value.metric_id = metric.id
                    value.save(using=to_db_id)
    
    # transfer topics, topic names, and topic name schemes
    with transaction.commit_on_success():
        analyses = Analysis.objects.using(to_db_id).filter(dataset__name=dataset_id)
        to_topic_name_schemes = TopicNameScheme.objects.using(to_db_id).all()
        for analysis in analyses:
            if not Topic.objects.using(to_db_id).filter(analysis_id=analysis).exists():
                topics = Topic.objects.using(from_db_id).filter(analysis__name=analysis.name)
                for topic in topics:
                    topic_names = TopicName.objects.using(from_db_id).filter(topic_id=topic.id)
                    topic.id = None
                    topic.analysis_id = analysis.id
                    topic.save(using=to_db_id)
                    for name in topic_names:
                        name.id = None
                        name.topic_id = topic.id
                        name_scheme, _ = to_topic_name_schemes.get_or_create(name=name.name_scheme.name, analysis_id=analysis.id)
                        name.name_scheme_id = name_scheme.id
                        name.save(using=to_db_id)
    
    
                        

            
    
    print('Done')




























# vim: et sw=4 sts=4
