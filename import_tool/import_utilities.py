from __future__ import print_function

import os
import json
import random
import re
import codecs

from topic_modeling import settings
from django.core.management import call_command
settings.DEBUG = False # Disable debugging to prevent the database layer from caching queries and thus hogging memory
# set Django Settings
# the 'DJANGO_SETTINGS_MODULE' must be set before the database can be used.
os.environ['DJANGO_SETTINGS_MODULE'] = 'topic_modeling.settings'

from import_scripts import database_import
from import_scripts import metadata
from analysis_scripts import analysis_import
from analysis_scripts import mallet
from helper_scripts.name_schemes.top_n import TopNTopicNamer
from metric_scripts import import_metrics

from dataset_classes.generic_dataset import (GenericDataset, GenericDocument, GenericSubdocument)
from dataset_classes.generic_tools import GenericTools

from topic_modeling.visualize.models import (Dataset, Analysis, TopicNameScheme, ExternalDataset)

def get_common_working_directories(dataset_identifier):
    """
    Create commonly used directory paths.
    Return a dictionary with 'working', 'dataset', and 'documents' that map to the correct directory.
    """
    topical_guide_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    working_dir = os.path.join(topical_guide_dir, 'working')
    if not os.path.exists(working_dir):
        os.makedirs(working_dir)
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
    """
    Run all metrics; an analysis is required for this process.
    """
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


# TODO make this a little bit more modular and better documented
# for example, the method could take an AbstractNamer type object
#~ def name_topics(database_id, dataset, analysis_settings, analysis_db):
    #~ '''\
    #~ Names all of the topics.
    #~ '''
    #~ if not TopicNameScheme.objects.using(database_id).filter(analysis=analysis_db, name=topic_namer.get_identifier()).exists():
        #~ topic_namer = TopNTopicNamer(database_id, dataset.get_identifier(), 
                                     #~ analysis_settings.get_analysis_name(), 3)
        #~ topic_namer.name_all_topics()


    

#~ def import_dataset2(dataset, analysis_settings, database_info=None):
    #~ '''\
    #~ Imports the dataset described by 'dataset' (which should be of type \
    #~ DataSetImportTask).  The dataset will be imported into the database \
    #~ described by database_info.
    #~ '''
    #~ 
    #~ # print a nice header message
    #~ 
    #~ 
    #~ # create commonly used directory paths
    #~ topical_guide_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    #~ working_dir = os.path.join(topical_guide_dir, 'working')
    #~ if not os.path.exists(working_dir):
        #~ os.makedirs(working_dir)
    #~ dataset_dir = os.path.join(working_dir, 'datasets', dataset.get_identifier()) # not the directory containing the source dataset information
    #~ if not os.path.exists(dataset_dir):
        #~ os.makedirs(dataset_dir)
    #~ document_dir = os.path.join(dataset_dir, 'files')
    #~ if not os.path.exists(document_dir):
        #~ os.makedirs(document_dir)
    #~ metadata_dir = os.path.join(dataset_dir, 'metadata')
    #~ if not os.path.exists(metadata_dir):
        #~ os.makedirs(metadata_dir)
    
    # creates the database and needed tables
    #~ print('Ensuring database and tables exist...')
    #~ database_id = run_migrate(dataset.get_identifier(), database_info)
    #~ 
    #~ # move the dataset data to a stable location on the server
    #~ print('Importing data from dataset object...')
    #~ transfer_dataset(database_id, dataset, analysis_settings, dataset_dir, document_dir)
    #~ dataset_db = Dataset.objects.using(database_id).get(name=dataset.get_identifier())
    #~ 
    #~ # depends on transfer_data()
    #~ print('Preparing mallet input file...')
    #~ prepare_mallet_input(dataset_dir, document_dir)
    #~ 
    #~ # depends on prepare_mallet_input()
    #~ print('Running mallet...')
    #~ run_mallet(analysis_settings, dataset_dir, document_dir, topical_guide_dir)
    #~ 
    #~ # depends on run_mallet()
    #~ print('Importing analysis...')
    #~ import_analysis(database_id, dataset, analysis_settings, topical_guide_dir, dataset_dir, analysis_settings.get_metadata_filenames(metadata_dir))
    #~ # TODO from here down the database isn't updated
    #~ # create commonly used database object(s)
    #~ analysis_db = Analysis.objects.using(database_id).get(name=analysis_settings.get_analysis_name(), 
                                         #~ dataset__name=dataset.get_identifier())
    #~ 
    #~ 
    #~ # depends on import_analysis()
    #~ print('Naming schemes...')
    #~ name_topics(database_id, dataset, analysis_settings, analysis_db)
    #~ 
    #~ dataset_name = dataset.get_identifier()
    #~ analysis_name = analysis_settings.get_analysis_name()
    #~ # Compute metrics
    #~ # the following depend on import_analysis()
    #~ print('Dataset metrics...')
    #~ dataset_metrics(database_id, dataset_name, analysis_name) # depends on import_dataset_into_database()
    #~ print('Analysis metrics...')
    #~ analysis_metrics(database_id, dataset_name, analysis_name, analysis_db)
    #~ print('Topic metrics...')
    #~ topic_metrics(database_id, analysis_settings.get_topic_metrics(), dataset_name, analysis_name, analysis_db, analysis_settings.get_topic_metric_args())
    #~ print('Pairwise topic metrics...')
    #~ pairwise_topic_metrics(database_id, analysis_settings.get_pairwise_topic_metrics(), dataset_name, analysis_name, analysis_db)
    #~ print('Document metrics...')
    #~ document_metrics(database_id, dataset_name, analysis_name, analysis_db)
    #~ print('Pairwise document metrics...')
    #~ pairwise_document_metrics(database_id, analysis_settings.get_pairwise_document_metrics(), dataset_name, analysis_name, analysis_db)


# vim: et sw=4 sts=4
