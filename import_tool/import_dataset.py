from __future__ import print_function

import os
import json
import codecs
import re

from topic_modeling import settings
from django.core.management import call_command
settings.DEBUG = False # Disable debugging to prevent the database layer from caching queries and thus hogging memory

from mallet import (prepare_mallet_input, run_mallet)
from import_metrics import *

# configure Django Settings
# NOTE: The 'DJANGO_SETTINGS_MODULE' must be set before 'dataset_import'
# can be imported/used.
os.environ['DJANGO_SETTINGS_MODULE'] = 'topic_modeling.settings'

from import_scripts.database_import import (create_dataset_db_entry, 
    import_documents_into_database, import_document_word_tokens)

from import_scripts import dataset_import, analysis_import
from import_scripts.metadata import (import_dataset_metadata_into_database,
    import_document_metadata_into_database)

from helper_scripts.name_schemes.top_n import TopNTopicNamer

from dataset_classes.generic_dataset import GenericDataset, GenericDocument, GenericSubdocument
from dataset_classes.generic_tools import GenericTools

from topic_modeling.visualize.models import (Dataset, TopicMetric,
    PairwiseTopicMetric, DocumentMetric, PairwiseDocumentMetric, 
    TopicNameScheme)
from topic_modeling.visualize.models import (Analysis, DatasetMetric,
    AnalysisMetric, DatasetMetricValue, AnalysisMetricValue,
    DatasetMetaInfoValue, DocumentMetaInfoValue, WordTypeMetaInfoValue,
    WordTokenMetaInfoValue, AnalysisMetaInfoValue, TopicMetaInfoValue,
    WordType, WordToken, Document, Topic, PairwiseTopicMetricValue,
    DocumentMetricValue)

def run_migrate(dataset_identifier, database_info):
    '''\
    Makes sure that the database is created and the tables exist.
    Returns the identifier the import process should use.
    '''
    if database_info:
        settings.DATABASES[dataset_identifier] = database_info
        identifier = dataset_identifier
    else:
        identifier = 'default'
    
    call_command('syncdb', database=identifier)
    return identifier


def document_info_collector(args, doc):
    '''\
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
    '''
    doc_id = doc.get_identifier()
    # get document full path
    full_path = os.path.join(args['doc_dir'], doc_id)
    args['doc_identifiers'][doc_id] = full_path
    # get metadata
    args['doc_metadata'][doc_id] = doc.get_metadata()
    # get words
    content = doc.get_content()
    args['words'][doc_id] = []
    words = args['words'][doc_id]
    for word_index, match in enumerate(re.finditer(args['token_regex'], content)):
        word = match.group().lower()
        start = match.start()
        words.append((word, word_index, start))
    # copy content to new location
    with open(full_path, 'w') as f:
        f.write(content)

def transfer_dataset(database_id, dataset, analysis_settings, dataset_dir, document_dir, metadata_dir):
    '''\
    Transfers the dataset's documents and metadata into files located on the server where the import process will continue.
    Ex: $TOPICAL_GUIDE_ROOT/working/datasets/files
        $TOPICAL_GUIDE_ROOT/working/datasets/metadata/documents.json
    '''
    # create database entry for dataset
    create_dataset_db_entry(database_id, 
                            dataset.get_identifier(),
                            dataset.get_readable_name(),
                            dataset.get_description(), 
                            dataset_dir, 
                            document_dir)
    
    
    # transfer all documents and collect document info
    args = {'doc_identifiers': {}, 
            'words': {}, 
            'doc_metadata': {}, 
            'doc_dir': document_dir,
            'token_regex': r'[a-zA-Z]+'}
    GenericTools.walk_documents(dataset, document_info_collector, args)
    
    # create entries for each document
    import_documents_into_database(database_id, dataset.get_identifier(), args['doc_identifiers'])
    
    # import words into database
    import_document_word_tokens(database_id, dataset.get_identifier(), args['words'])
    
    dataset_db = Dataset.objects.using(database_id).get(name=dataset.get_identifier())
    
    # write the dataset metadata to the database
    dataset_metadata = dataset.get_metadata()
    dataset_metadata_types = {}
    GenericTools.collect_types(dataset_metadata_types, dataset_metadata)
    print('Importing dataset metadata into database...')
    import_dataset_metadata_into_database(database_id, dataset_db, dataset_metadata, 
                                          dataset_metadata_types)
                                          
    # write the document metadata to the database
    all_doc_metadata = args['doc_metadata']
    all_document_metadata_types = {}
    for key, value in all_doc_metadata.items():
        GenericTools.collect_types(all_document_metadata_types, value)
    print('Importing document metadata into database...')
    import_document_metadata_into_database(database_id, dataset_db, all_doc_metadata,
                                           all_document_metadata_types)
    


# TODO any analysis could be genericized, would it be worth while?
def import_analysis(database_id, dataset, analysis_settings, topical_guide_dir, dataset_dir, metadata_filenames):
    '''\
    Imports the analysis by creating a DataSet object, Analysis DB object,
    a Metadata dictionary, and parses the mallet_output file.
    '''
    c = analysis_settings.get_mallet_configurations(topical_guide_dir, dataset_dir)
    c['analysis_name'] = analysis_settings.get_analysis_name()
    c['analysis_readable_name'] = analysis_settings.get_analysis_readable_name()
    c['analysis_description'] = analysis_settings.get_analysis_description()
    c['markup_dir'] = os.path.join(dataset_dir, c['analysis_name']) + '-markup'
    analysis_import.import_analysis(database_id,
                                    dataset.get_identifier(), 
                                    c['analysis_name'], 
                                    c['analysis_readable_name'], 
                                    c['analysis_description'],
                                    c['markup_dir'], 
                                    c['mallet_output'], 
                                    c['mallet_input'], 
                                    metadata_filenames, 
                                    r'[A-Za-z]+',
                                    analysis_settings.get_number_of_topics())

# TODO clarify/update documentation for this method
#~ def import_metadata(dataset, dataset_db, metadata_filenames):
    #~ '''\
    #~ Appears to import the metadata into the database.
    #~ '''
    #~ 
    #~ if os.path.exists(metadata_filenames['documents']):
        #~ skip_import_dataset_metadata = False
        #~ try:
            #~ skip_import_dataset_metadata = DocumentMetaInfoValue.objects.filter(
                                            #~ document__dataset=dataset_db).count() > 0
        #~ except Dataset.DoesNotExist:
            #~ skip_import_dataset_metadata = False
        #~ 
        #~ if not skip_import_dataset_metadata:
            #~ metadata = Metadata(metadata_filenames['documents'])
            #~ try:
                #~ import_document_metadata(dataset_db, metadata)
            #~ except Exception as e:
                #~ try: 
                    #~ for doc in dataset_db.documents.all():
                        #~ doc.metainfovalues.all().delete()
                #~ except Dataset.DoesNotExist:
                    #~ pass
                #~ raise e
    #~ 
    #~ # as far as I can tell the code below will never get executed
    #~ # additionally there was no readily available documentation as to their function
    #~ # TODO findout why the other files don't exist, or if there
    #~ # is functionality that is missing or latent in the import process
    #~ # TODO some of the backend.py code for checking if a task was
    #~ # done wasn't moved over (mostly because this code appears to be dead
    #~ 
    #~ if os.path.exists(metadata_filenames['word_types']):
        #~ metadata = Metadata(metadata_filenames['word_types'])
        #~ try:
            #~ import_word_type_metadata(dataset_db, metadata)
        #~ except Exception as e:
            #~ try:
                #~ for word_type in WordType.objects.filter(tokens__doc__dataset=dataset_db):
                    #~ word_type.metainfovalues.all().delete()
            #~ except Dataset.DoesNotExist:
                #~ pass
            #~ raise e
    #~ 
    #~ if os.path.exists(metadata_filenames['word_tokens']):
        #~ metadata = Metadata(metadata_filenames['word_tokens'])
        #~ try:
            #~ import_word_token_metadata(dataset_db, metadata)
        #~ except Exception as e:
            #~ try:
                #~ for word_token in WordToken.objects.filter(doc__dataset=dataset_db):
                    #~ word_token.metainfovalues.all().delete()
            #~ except Dataset.DoesNotExist:
                #~ pass
            #~ raise e
    #~ 
    #~ analysis_settings = dataset.get_analysis_settings()
    #~ analysis_db = Analysis.objects.get(name=analysis_settings.get_analysis_name(), 
                                      #~ dataset__name=dataset.get_dataset_identifier())
    #~ 
    #~ if os.path.exists(metadata_filenames['analysis']):
        #~ metadata = Metadata(metadata_filenames['analysis'])
        #~ try:
            #~ import_analysis_metadata(analysis_db, metadata)
        #~ except Exception as e:
            #~ try:
                #~ analysis_db.metainfovalues.all().delete()
            #~ except Analysis.DoesNotExist:
                #~ pass
            #~ raise e
            #~ 
    #~ if os.path.exists(metadata_filenames['topics']):
        #~ metadata = Metadata(metadata_filenames['topics'])
        #~ try:
            #~ import_topic_metadata(analysis_db, metadata)
        #~ except Exception as e:
            #~ try:
                #~ for topic in analysis().topics.all():
                    #~ topic.metainfovalues.all().delete()
            #~ except Analysis.DoesNotExist:
                #~ pass
            #~ raise e

def scheme_in_database(name_scheme_name, analysis_db):
    '''\
    Helper function for name_schemes().
    '''
    try:
        TopicNameScheme.objects.get(analysis=analysis_db, name=name_scheme_name)
        return True
    except (Dataset.DoesNotExist, Analysis.DoesNotExist, TopicNameScheme.DoesNotExist):
        return False

# TODO update documentation to be more specific
def name_schemes(dataset, analysis_settings, analysis_db):
    '''\
    Names all topics based on a particular scheme.
    '''
    
    name_schemes = [TopNTopicNamer(dataset.get_identifier(), 
                    analysis_settings.get_analysis_name(), 3)]
    
    for ns in name_schemes:
        if not scheme_in_database(ns.scheme_name().split(':')[-1], analysis_db):
            ns.name_all_topics()




def import_dataset(dataset, analysis_settings, database_info=None):
    '''\
    Imports the dataset described by 'dataset' (which should be of type \
    DataSetImportTask).  The dataset will be imported into the database \
    described by database_info.
    '''
    
    # print a nice header message
    print()
    print('----- Topical Guide Import System -----')
    print('Importing ' + dataset.get_readable_name())
    print()
    
    # create commonly used directory paths
    topical_guide_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    working_dir = os.path.join(topical_guide_dir, 'working')
    if not os.path.exists(working_dir):
        os.makedirs(working_dir)
    dataset_dir = os.path.join(working_dir, 'datasets', dataset.get_identifier()) # not the directory containing the source dataset information
    if not os.path.exists(dataset_dir):
        os.makedirs(dataset_dir)
    document_dir = os.path.join(dataset_dir, 'files')
    if not os.path.exists(document_dir):
        os.makedirs(document_dir)
    metadata_dir = os.path.join(dataset_dir, 'metadata')
    if not os.path.exists(metadata_dir):
        os.makedirs(metadata_dir)
    
    # creates the database and needed tables
    print('Ensuring database and tables exist...')
    database_id = run_migrate(dataset.get_identifier(), database_info)
    
    # move the dataset data to a stable location on the server
    print('Importing data from dataset object...')
    transfer_dataset(database_id, dataset, analysis_settings, dataset_dir, document_dir, metadata_dir)
    dataset_db = Dataset.objects.get(name=dataset.get_identifier())
    
    # depends on transfer_data()
    print('Preparing mallet input file...')
    prepare_mallet_input(dataset_dir, document_dir)
    
    # depends on prepare_mallet_input()
    print('Running mallet...')
    run_mallet(analysis_settings, dataset_dir, document_dir, topical_guide_dir)
    
    # depends on run_mallet()
    print('Importing analysis...')
    import_analysis(database_id, dataset, analysis_settings, topical_guide_dir, dataset_dir, analysis_settings.get_metadata_filenames(metadata_dir))
    # TODO from here down the database isn't updated
    # create commonly used database object(s)
    analysis_db = Analysis.objects.using(database_id).get(name=analysis_settings.get_analysis_name(), 
                                         dataset__name=dataset.get_identifier())
    
    
    # depends on import_analysis()
    print('Naming schemes...')
    name_schemes(dataset, analysis_settings, analysis_db)
    
    dataset_name = dataset.get_identifier()
    analysis_name = analysis_settings.get_analysis_name()
    # Compute metrics
    # the following depend on import_analysis()
    print('Dataset metrics...')
    dataset_metrics(dataset_name, analysis_name) # depends on import_dataset_into_database()
    print('Analysis metrics...')
    analysis_metrics(dataset_name, analysis_name, analysis_db)
    print('Topic metrics...')
    topic_metrics(analysis_settings.get_topic_metrics(), dataset_name, analysis_name, analysis_db, analysis_settings.get_topic_metric_args())
    print('Pairwise topic metrics...')
    pairwise_topic_metrics(analysis_settings.get_pairwise_topic_metrics(), dataset_name, analysis_name, analysis_db)
    print('Document metrics...')
    document_metrics(dataset_name, analysis_name, analysis_db)
    print('Pairwise document metrics...')
    pairwise_document_metrics(analysis_settings.get_pairwise_document_metrics(), dataset_name, analysis_name, analysis_db)


# vim: et sw=4 sts=4
