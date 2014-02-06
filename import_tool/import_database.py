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
# NOTE: The 'DJANGO_SETTINGS_MODULE' must be set before dataset_import 
# can be imported.
os.environ['DJANGO_SETTINGS_MODULE'] = 'topic_modeling.settings'

# import utilities
from import_scripts import dataset_import, analysis_import
from import_scripts.metadata import (Metadata, import_dataset_metadata,
    import_document_metadata, import_word_type_metadata, 
    import_word_token_metadata, import_analysis_metadata, import_topic_metadata)

from helper_scripts.name_schemes.top_n import TopNTopicNamer

from tasks.general_task import DataSetImportTask

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




#TODO eradicate dependence on the config and backend script

#TODO eliminate doit
#~ Backend Running Sequence:
#~ 
#~ -- extract_data # done
#~ -- mallet_input # done
#~ -- dataset_import # done
#~ -- mallet_imported_data # done
#~ -- mallet_output_gz # done
#~ -- mallet_output # done
#~ -- analysis_import # done
#~ -- metadata_import:word_tokens # done
#~ -- metadata_import:word_types # done
#~ -- metadata_import:datasets # done
#~ -- metadata_import:documents # done
#~ -- metadata_import:analysis # done
#~ -- metadata_import:topics # done
#~ -- name_schemes:Top3 # done
#~ -- dataset_metrics:counts # next
#~ -- analysis_metrics:entropy
#~ -- topic_metrics:word_entropy # next 2
#~ -- topic_metrics:token_count # next 2
#~ -- topic_metrics:type_count # next 2
#~ -- topic_metrics:document_entropy # next 2
#~ -- pairwise_topic_metrics:document_correlation
#~ -- pairwise_topic_metrics:word_correlation
#~ -- document_metrics:topic_entropy # next
#~ -- document_metrics:token_count # next
#~ -- document_metrics:type_count # next
#~ -- pairwise_document_metrics:topic_correlation
#~ .  hash_java
#~ -- compile_java
#~ -- graphs:Top3

def transfer_data(dataset, dataset_dir, document_dir):
    '''/
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
    Imports the dataset describle by 'dataset' (which should be of type DataSetImportTask).
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
    
    
    from metric_scripts.datasets import metrics
    dataset_name = dataset.get_dataset_name()
    analysis_name = analysis_settings.get_analysis_name()
    # Compute metrics
    # depends on import_dataset_into_database()
    print('Dataset metrics...')
    dataset_metrics(metrics, dataset_name, analysis_name)
    
    # depends on import_analysis()
    print('Analysis metrics...')
    analysis_metrics(metrics, dataset_name, analysis_name, analysis_db)
    
    # depends on import_analysis()
    print('Topic metrics...')
    topic_metrics(metrics, dataset_name, analysis_name, analysis_db)
    
    # depends on import_analysis()
    print('Pairwise topic metrics...')
    pairwise_topic_metrics(metrics, dataset_name, analysis_name)
    
    # depends on import_analysis()
    print('Document metrics...')
    document_metrics(metrics, dataset_name, analysis_name)
    
    # depends on import_analysis()
    print('Pairwise document metrics...')
    pairwise_document_metrics(metrics, dataset_name, analysis_name)
    
    
    
    
    
    #the usual doit processes will run after this line
    # TODO delete the following after doit is stripped out
    #~ try:
        #~ from import_tool.local_settings import LOCAL_DIR
    #~ except ImportError:
        #~ raise Exception("Import error looking for local_settings.py. "
                #~ "Look at import_tool/local_settings.py.sample for help")
    #~ DB_BASE = os.path.join(LOCAL_DIR, '.dbs')
    #~ if not os.path.exists(DB_BASE):
        #~ os.mkdir(DB_BASE)
    #~ sys.path.append("tools/doit")
    #~ from doit.doit_cmd import cmd_main
    #~ path = os.path.abspath('import_tool/backend.py')
#~ 
    #~ #The database file where we'll store info about this build
    #~ db_name = os.path.join(DB_BASE, "{0}.db".format("Conference_Talks_on_Agency".replace('/','_')))
#~ 
    #~ args = ['-f', path] + ['--db', db_name]
    #~ res = cmd_main(args)


# vim: et sw=4 sts=4
