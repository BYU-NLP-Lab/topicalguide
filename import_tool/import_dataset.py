#!/usr/bin/python
## -*- coding: utf-8 -*-

from __future__ import print_function

# general utilities
import os
import json
import codecs

from topic_modeling import settings
settings.DEBUG = False # Disable debugging to prevent the database layer from caching queries and thus hogging memory

from mallet import (prepare_mallet_input, run_mallet)
from import_metrics import *

# configure Django Settings
# NOTE: The 'DJANGO_SETTINGS_MODULE' must be set before 'dataset_import'
# can be imported.
os.environ['DJANGO_SETTINGS_MODULE'] = 'topic_modeling.settings'

# import process utilities
from import_scripts import dataset_import, analysis_import
from import_scripts.metadata import (Metadata, import_dataset_metadata,
    import_document_metadata, import_word_type_metadata, 
    import_word_token_metadata, import_analysis_metadata, import_topic_metadata)

from helper_scripts.name_schemes.top_n import TopNTopicNamer

from dataset_classes.generic_dataset import DataSetImportTask

from topic_modeling.visualize.models import (Dataset, TopicMetric,
    PairwiseTopicMetric, DocumentMetric, PairwiseDocumentMetric, 
    TopicNameScheme)
from topic_modeling.visualize.models import (Analysis, DatasetMetric,
    AnalysisMetric, DatasetMetricValue, AnalysisMetricValue,
    DatasetMetaInfoValue, DocumentMetaInfoValue, WordTypeMetaInfoValue,
    WordTokenMetaInfoValue, AnalysisMetaInfoValue, TopicMetaInfoValue,
    WordType, WordToken, Document, Topic, PairwiseTopicMetricValue,
    DocumentMetricValue)

from build import create_dirs_and_open # TODO add this to a general toolset


# TODO fix dataset metadata
# SOLUTION import the dataset metadata into database, this may require refactoring to make it elegant
# TODO fix document metadata, which isn't being imported into the database correctly
# TODO database table 'pairwisedocumentmetric' has extra entry 'Word Correlation'
#       which should be under 'pairwisetopicmetric'

# TODO make sure mallet doesn't stop the process to ask if you want to override a file
# TODO make sure that anything (like 'year') is converted to an int in metadata (if needed)
# TODO while importing a KeyError is thrown for u'a' as the key, find the cause


def transfer_data(dataset, dataset_dir, document_dir):
    '''\
    Transfers the dataset's documents and metadata into files located on the server.
    Ex: $TOPICAL_GUIDE_ROOT/working/datasets/files
        $TOPICAL_GUIDE_ROOT/working/datasets/metadata/documents.json
    '''
        
    # copy the documents over
    dataset.copy_contents_to_directory(document_dir)
    
    # copy the metadata over
    metadata_file_name = os.path.join(dataset_dir, 'metadata', 'documents') + '.json'
    w = create_dirs_and_open(metadata_file_name)
    metadata = {'types':dataset.get_document_metadata_types(), \
                'data':dataset.get_all_documents_metadata()}
    w.write(json.dumps(metadata))
    w.close()



# TODO apparently the words are iterated over twice (according to 
# another comment in backend.py). Look into this and find out what is going on
# and whether or not this is really a problem/concern.
def import_dataset_into_database(dataset, dataset_dir, document_dir, metadata_filenames):
    '''\
    Imports the given dataset in to the database. Includes creating a
    Dataset object, WordType objects for each word
    '''
    
    # checks if the dataset exists, 
    # TODO uncomment later after importing to the database works
    if not dataset_import.check_dataset(dataset.get_dataset_name()):
        dataset_import.import_dataset(dataset.get_dataset_name(),
                                      dataset.get_dataset_readable_name(),
                                      dataset.get_description(),
                                      metadata_filenames,
                                      dataset_dir,
                                      document_dir,
                                      r'[A-Za-z]+')

def import_analysis(dataset, topical_guide_dir, dataset_dir, metadata_filenames):
    '''\
    Imports the analysis by creating a DataSet object, Analysis DB object,
    a Metadata dictionary, and parses the mallet_output file.
    '''
    
    analysis_settings = dataset.get_analysis_settings()
    c = analysis_settings.get_mallet_configurations(topical_guide_dir, dataset_dir)
    c['analysis_name'] = analysis_settings.get_analysis_name()
    c['analysis_readable_name'] = analysis_settings.get_analysis_readable_name()
    c['analysis_description'] = analysis_settings.get_analysis_description()
    c['markup_dir'] = os.path.join(dataset_dir, c['analysis_name']) + '-markup'
    analysis_import.import_analysis(dataset.get_dataset_name(), 
                                    c['analysis_name'], 
                                    c['analysis_readable_name'], 
                                    c['analysis_description'],
                                    c['markup_dir'], 
                                    c['mallet_output'], 
                                    c['mallet_input'], 
                                    metadata_filenames, 
                                    r'[A-Za-z]+')

# TODO clarify/update documentation for this method
def import_metadata(dataset, dataset_db, metadata_filenames):
    '''\
    Appears to import the metadata into the database.
    '''
    
    if os.path.exists(metadata_filenames['documents']):
        skip_import_dataset_metadata = False
        try:
            skip_import_dataset_metadata = DocumentMetaInfoValue.objects.filter(
                                            document__dataset=dataset_db).count() > 0
        except Dataset.DoesNotExist:
            skip_import_dataset_metadata = False
        
        if not skip_import_dataset_metadata:
            metadata = Metadata(metadata_filenames['documents'])
            try:
                import_document_metadata(dataset_db, metadata)
            except Exception as e:
                try: 
                    for doc in dataset_db.documents.all():
                        doc.metainfovalues.all().delete()
                except Dataset.DoesNotExist:
                    pass
                raise e
    
    
    # as far as I can tell the code below will never get executed
    # additionally there was no readily available documentation as to their function
    # TODO findout why the other files don't exist, or if there
    # is functionality that is missing or latent in the import process
    # TODO some of the backend.py code for checking if a task was
    # done wasn't moved over (mostly because this code appears to be dead
    if os.path.exists(metadata_filenames['datasets']):
        metadata = Metadata(metadata_filenames['datasets'])
        try:
            import_dataset_metadata(dataset_db, metadata)
        except Exception as e:
            try:
                dataset_db.metainfovalues.all().delete()
            except Dataset.DoesNotExist:
                pass
            raise e
    
    if os.path.exists(metadata_filenames['word_types']):
        metadata = Metadata(metadata_filenames['word_types'])
        try:
            import_word_type_metadata(dataset_db, metadata)
        except Exception as e:
            try:
                for word_type in WordType.objects.filter(tokens__doc__dataset=dataset_db):
                    word_type.metainfovalues.all().delete()
            except Dataset.DoesNotExist:
                pass
            raise e
    
    if os.path.exists(metadata_filenames['word_tokens']):
        metadata = Metadata(metadata_filenames['word_tokens'])
        try:
            import_word_token_metadata(dataset_db, metadata)
        except Exception as e:
            try:
                for word_token in WordToken.objects.filter(doc__dataset=dataset_db):
                    word_token.metainfovalues.all().delete()
            except Dataset.DoesNotExist:
                pass
            raise e
    
    analysis_settings = dataset.get_analysis_settings()
    analysis_db = Analysis.objects.get(name=analysis_settings.get_analysis_name(), 
                                      dataset__name=dataset.get_dataset_name())
    
    if os.path.exists(metadata_filenames['analysis']):
        metadata = Metadata(metadata_filenames['analysis'])
        try:
            import_analysis_metadata(analysis_db, metadata)
        except Exception as e:
            try:
                analysis_db.metainfovalues.all().delete()
            except Analysis.DoesNotExist:
                pass
            raise e
            
    if os.path.exists(metadata_filenames['topics']):
        metadata = Metadata(metadata_filenames['topics'])
        try:
            import_topic_metadata(analysis_db, metadata)
        except Exception as e:
            try:
                for topic in analysis().topics.all():
                    topic.metainfovalues.all().delete()
            except Analysis.DoesNotExist:
                pass
            raise e

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
    
    name_schemes = [TopNTopicNamer(dataset.get_dataset_name(), 
                    analysis_settings.get_analysis_name(), 3)]
    
    for ns in name_schemes:
        if not scheme_in_database(ns.scheme_name().split(':')[-1], analysis_db):
            ns.name_all_topics()



def import_dataset(dataset):
    '''\
    Imports the dataset described by 'dataset' (which should be of type DataSetImportTask).
    '''
    
    analysis_settings = dataset.get_analysis_settings()
    
    # print a friendly message
    print()
    print("----- Topical Guide Data Import System -----")
    print("Dataset name: " + dataset.get_dataset_readable_name())
    print("Creator: " + dataset.get_dataset_creator())
    print("Source: " + dataset.get_dataset_source())
    print()
    
    from import_tool.local_settings import LOCAL_DIR
    # create commonly used directory paths
    topical_guide_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    dataset_dir = os.path.join(LOCAL_DIR, 'datasets', dataset.get_dataset_name())
    if not os.path.exists(dataset_dir):
        os.mkdir(dataset_dir)
    document_dir = os.path.join(dataset_dir, 'files')
    if not os.path.exists(document_dir):
        os.mkdir(document_dir)
    metadata_dir = os.path.join(dataset_dir, 'metadata')
    # create database directory
    database_dir = os.path.join(LOCAL_DIR, '.dbs')
    if not os.path.exists(database_dir):
        os.mkdir(database_dir)
    # TODO it appears that the database made specifically for this import
    # is never actually used, getting it working would allow for easy transporting
    # of pre-imported datasets
    database_file = os.path.join(database_dir, dataset.get_dataset_name() + '.db')
    
    
    # Move the dataset data to a stable location on the server.
    print('Copying data from dataset object...')
    transfer_data(dataset, dataset_dir, document_dir)
    
    # TODO either the DataSetImportTask needs to strip out punctuation, xml tags, etc.
    # TODO or we need to do it in this function
    # depends on transfer_data()
    print('Preparing mallet input file...')
    prepare_mallet_input(dataset_dir, document_dir)
    
    # TODO it appears that mallet is not using the document prepared for it
    # TODO in the previous function, find out why and adjust accordingly
    # depends on prepare_mallet_input()
    print('Running mallet...')
    run_mallet(analysis_settings, dataset_dir, document_dir, topical_guide_dir)
    
    # depends on transfer_data()
    print('Importing dataset into database.')
    import_dataset_into_database(dataset, dataset_dir, document_dir, analysis_settings.get_metadata_filenames(metadata_dir))
    
    # TODO this name (below) seems to be misleading as to what is going on
    # depends on run_mallet()
    print('Importing analysis...')
    import_analysis(dataset, topical_guide_dir, dataset_dir, analysis_settings.get_metadata_filenames(metadata_dir))
    
    # create commonly used database objects
    dataset_db = Dataset.objects.get(name=dataset.get_dataset_name())
    analysis_db = Analysis.objects.get(name=analysis_settings.get_analysis_name(), 
                                       dataset__name=dataset.get_dataset_name())
    
    # depends on import_analysis()
    print('Importing metadata...')
    import_metadata(dataset, dataset_db, analysis_settings.get_metadata_filenames(metadata_dir))
    
    # depends on import_analysis()
    print('Naming schemes...')
    name_schemes(dataset, analysis_settings, analysis_db)
    
    
    dataset_name = dataset.get_dataset_name()
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
