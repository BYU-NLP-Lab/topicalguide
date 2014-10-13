#!/usr/bin/env python

from __future__ import print_function

import os
from os.path import isfile, isdir, isabs
import argparse
import time
import datetime

from import_tool import import_utilities
from import_tool import basic_tools
from import_tool.dataset_scripts.generic_dataset import GenericDataset
from import_tool.dataset_scripts.json_dataset import JsonDataset
from import_tool.dataset_scripts.wikipedia_dataset import WikipediaDataset
from import_tool.analysis_scripts.mallet_analysis import MalletLdaAnalysis

# For example usage see the README.
# For help:
# python topicalguide.py -h

topical_guide_dir = os.path.abspath(os.path.dirname(__file__))
working_dir = os.environ['TOPICAL_GUIDE_WORKING_DIR'] or os.path.join(topical_guide_dir, 'working')

def get_database_configurations(file_path):
    """
    Get the database configurations, an error is thrown if the \
    file cannot be read or is not found.
    If the contents don't make sense return an empty dictionary.
    For relative filenames, the folder they will be relative to is \
    the working directory.
    """
    database_config = {}
    
    key_names = ['ENGINE', 'NAME', 'HOST', 'OPTIONS', 'PASSWORD', 'PORT', 'USER']
    with open(file_path, 'r') as f:
        database_config = basic_tools.metadata_to_dict(f.read()) # read in the database configurations
    # make sure the key names are upper case
    for key in key_names:
        if key.lower() in database_config:
            database_config[key] = database_config[key.lower()]
            del database_config[key.lower()]
    # make sure that the relative path is relative to the working directory
    if 'NAME' in database_config and not isdir(database_config['NAME']):
        if not os.path.isabs(database_config['NAME']): # create an absolute path if a relative one is specified
            database_config['NAME'] = os.path.join(working_dir, database_config['NAME'])
    
    return database_config


def get_dataset(args):
    """Read the args and return a dataset."""
    if args.dataset_class == 'GenericDataset':
        dataset = GenericDataset(args.dataset)
    elif args.dataset_class == 'JsonDataset':
        dataset = JsonDataset(args.dataset)
    else:
        raise Exception('Invalid dataset class.')
    
    if args.identifier:
        dataset.set_identifier(args.identifier)
    dataset.set_is_recursive(args.recursive)
    
    return dataset


def exec_check_dataset(args):
    """
    Check the dataset for blank documents and tell you what metadata types you have.
    """
    dataset = get_dataset(args)
    
    blank_documents = []
    blank_metadata = []
    metadata_types = {}

    for doc in dataset:
        content = doc.get_content()
        meta = doc.get_metadata()
        if content == '' or content == None: # collect blank documents
            blank_documents.append(doc.get_uri())
        if meta == {} or meta == None: # collect blank metadata
            blank_metadata.append(doc.get_uri())
        else: # collect metadata types
            basic_tools.collect_types(metadata_types, meta)
    
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
    basic_tools.collect_types(dataset_metadata_types, dataset.get_metadata())
    
    print('Dataset readable name: ')
    print('"' + dataset.readable_name + '"')
    print()
    
    print('Dataset description: ')
    print('"' + dataset.description + '"')
    print()
    
    if dataset_metadata_types:
        print('Listing of dataset metadata and their associated types: ')
        for key, value in dataset_metadata_types.items():
            print(key + ': ' + value)
    else:
        print('No dataset metadata.')
    print()
    
    if metadata_types:
        print('Listing of document metadata and their associated types: ')
        for key, value in metadata_types.items():
            print(key + ': ' + value)
    else:
        print('No document metdata')
    print()


def exec_import_dataset(args):
    """
    Perform basic checks and create necessary objects in preparation to import.
    Import dataset into database.
    Run the analysis and import results into the database.
    Run metrics and import results into the database.
    Return nothing.
    """
    # Get database configurations.
    database_info = None
    if args.database_config:
        database_info = get_database_configurations(args.database_config)
    
    # Create GenericDataset object and set settings.
    dataset = get_dataset(args)
    
    # Get common directories.
    directories = import_utilities.get_common_working_directories(dataset.get_identifier())
    
    # Make sure the tables exist in the database and get a database identifier.
    database_id = import_utilities.run_syncdb(database_info)
    # Make sure that the default database exists
    if database_id != 'default': # Check so syncdb isn't run twice in a row for no reason.
        import_utilities.run_syncdb(None)
    
    # Read in stopwords.
    stopwords = {}
    if args.stopwords:
        if isfile(args.stopwords):
            with open(args.stopwords, 'r') as s_file:
                for line in s_file:
                    line = unicode(line, encoding='utf-8', errors='ignore')
                    stopwords[line.strip().lower()] = True
        else:
            raise Exception('Invalid stopwords file.')
    
    # Start the import process
    dataset_name = import_utilities.import_dataset(database_id, dataset, directories, 
                                                   stopwords=stopwords, 
                                                   find_bigrams=args.bigrams,
                                                   keep_singletons=args.keep_singletons)


def get_analysis(args, directories):
    """Read the args and return a dataset."""
    if args.topic_modeling_tool == 'MalletLDA':
        analysis = MalletLdaAnalysis(directories['topical_guide'], directories['dataset'], args.number_of_topics)
        if args.subdocuments:
             analysis.set_create_subdocuments_method(basic_tools.create_subdocuments)
    else:
        raise Exception('Invalid topic modeling tool.')
    
    return analysis


def exec_run_analysis(args):
    """Run an analysis on the specified dataset."""
    # Get database configurations.
    database_info = None
    if args.database_config:
        database_info = get_database_configurations(args.database_config)
    
    # Make sure the tables exist in the database and get a database identifier.
    database_id = import_utilities.run_syncdb(database_info)
    # Make sure that the default database exists
    if database_id != 'default': # Check so syncdb isn't run twice in a row for no reason.
        import_utilities.run_syncdb(None)
    
    # Get common directories.
    directories = import_utilities.get_common_working_directories(args.dataset_identifier)
    
    # create analysis
    analysis = get_analysis(args, directories)
    
    # run an analysis
    analysis_identifier = import_utilities.run_analysis(database_id, args.dataset_identifier, analysis, directories)
    
    # run basic metrics on the analysis
    import_utilities.run_basic_metrics(database_id, args.dataset_identifier, analysis_identifier)


def exec_list(args):
    """List the datasets and analyses."""
    from topic_modeling.visualize.api import query_datasets
    options = { 
        'datasets': '*', 'dataset_attr': ['metadata'],
        'analyses': '*', 'analysis_attr': ['metadata'],
    }
    
    datasets = query_datasets(options)
    if len(datasets) == 0:
        print('No datasets in database.')
    else:
        print('Format is as follows:')
        print("dataset-identifier (dataset's-readable-name)")
        print("\tanalysis-identifier (analysis'-readable-name)")
        print()
        
        print('Datasets:')
        for dataset, items in datasets.iteritems():
            print(dataset+" ("+items['metadata']['readable_name']+")")
            analyses = items['analyses']
            if len(analyses) == 0:
                print('\tNo analyses available.')
            else:
                for analysis, items2 in analyses.iteritems():
                    print('\t'+analysis+" ("+items2['metadata']['readable_name']+")")


def exec_link(args):
    """Link a dataset to the default database."""
    database_info = get_database_configurations(args.database_config)
    
    # Make sure the tables exist in the database and get a database identifier.
    database_id = import_utilities.run_syncdb(database_info)
    # Make sure that the default database exists
    if database_id != 'default': # Check so syncdb isn't run twice in a row for no reason.
        import_utilities.run_syncdb(None)
    
    database_id = import_utilities.run_syncdb(database_info)
    import_utilities.link_dataset(database_id, args.dataset_name)


def exec_run_metrics(args):
    """Run the metrics on the given thing."""
    # Get database configurations.
    database_info = None
    if args.database_config:
        database_info = get_database_configurations(args.database_config)
    
    # Make sure the tables exist in the database and get a database identifier.
    database_id = import_utilities.run_syncdb(database_info)
    # Make sure that the default database exists
    if database_id != 'default': # Check so syncdb isn't run twice in a row for no reason.
        import_utilities.run_syncdb(None)
    
    if args.metrics:
        import_utilities.run_metrics(database_id, args.dataset_identifier, args.analysis_identifier, set(args.metrics))


def exec_migrate_dataset(args):
    """Move a dataset from one database to another."""
    dataset_id = args.dataset_name
    from_database = args.from_database
    to_database = args.to_database
    
    if from_database == to_database:
        print('The from database is the same as the to database.')
    
    # get database configurations
    from_database_config = None
    to_database_config = None
    if from_database != 'default':
        from_database_config = get_database_configurations(from_database)
    if to_database != 'default':
        to_database_config = get_database_configurations(to_database)
    
    # ensure that the working directory is created prior to syncdb
    import_utilities.make_working_dir()
    
    # make sure that both databases exist
    from_db_id = import_utilities.run_syncdb(from_database_config)
    to_db_id = import_utilities.run_syncdb(to_database_config)
    
    # run migrate
    import_utilities.migrate_dataset(dataset_id, from_db_id, to_db_id)


def exec_remove_metrics(args):
    """Remove listed metrics from dataset."""
    # Get database configurations.
    database_info = None
    if args.database_config:
        database_info = get_database_configurations(args.database_config)
    
    # Make sure the tables exist in the database and get a database identifier.
    database_id = import_utilities.run_syncdb(database_info)
    # Make sure that the default database exists
    if database_id != 'default': # Check so syncdb isn't run twice in a row for no reason.
        import_utilities.run_syncdb(None)
    
    import_utilities.remove_metrics(database_id, args.dataset_name, args.analysis_name, args.metrics)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    
    subparsers = parser.add_subparsers(title='subcommands',
                                       help='Type -h under each subcommand for additional help.')
    
    # Add database config file option to parser.
    def add_database_flag(parser):
        parser.add_argument('-d', '--database-config', type=str, action='store', default=None, 
                            help='Uses the database configurations from the given file.')
    
    # Used to allow the check command to have all of the same options as import.
    def add_import_flags(parser):
        parser.add_argument('-i', '--identifier', type=str, action='store', default=None, 
                               help='A unique name to import the dataset under (e.g. state_of_the_union.)')
        parser.add_argument('-r', '--recursive', action='store_true', default=False, 
                               help='Recursively look for documents in the given dataset\'s "documents" directory.')
        # TODO: Pre-preprocessing step, move to different command.
        #~ parser.add_argument('--remove-html-tags', action='store_true', default=False, 
                               #~ help='Removes html tags.')
        #~ parser.add_argument('--convert-html-entities', action='store_true', default=False, 
                               #~ help='Convert html entities to characters (e.g. &gt; converts to >).')
        parser.add_argument('-s', '--stopwords', type=str, action='store', default=None, 
                            help='Specify a file containing a carriage return separated list of words to exclude.')
        parser.add_argument('-k', '--keep-singletons', action='store_true', default=False, 
                            help='Keep word types that occur infrequently: count <= max(1, log(|documents|) - 2).')
        parser.add_argument('-b', '--bigrams', action='store_true', default=False, 
                            help='Specify whether or not to find bigrams as a preprocessing step.')
        parser.add_argument('-c', '--dataset-class', type=str, action='store', default='GenericDataset',
                            choices=['GenericDataset', 'JsonDataset'],
                            help='Optionally specify the dataset class used to interface with your documents.')
    
    # import command
    import_parser = subparsers.add_parser('import', help='Import a dataset using a built-in class.')
    import_parser.add_argument('dataset', type=str, help='Imports the dataset from the given directory.')
    add_database_flag(import_parser)
    add_import_flags(import_parser)
    import_parser.set_defaults(which='import')
    
    # check command
    check_parser = subparsers.add_parser('check', help='A utility that helps check the integrity of documents and metadata raising red flags if inconsistencies are found among the metadata keys or if there are any blank documents.')
    check_parser.add_argument('dataset', type=str, help="""\
                                                        The dataset to be checked for missing metadata, \
                                                        missing content, and prints info about the metadata \
                                                        types of the documents to aid in importing.
                                                        """)
    add_import_flags(check_parser)
    check_parser.set_defaults(which='check')
    
    # analysis command
    analysis_parser = subparsers.add_parser('analyze', help='Allows you to choose and run an analysis on an imported dataset. Note that the basic metrics will always be run.')
    analysis_parser.add_argument('dataset_identifier', type=str, help="""\
                                                                      The dataset identifier as printed at the \
                                                                      end of the import command or as shown in \
                                                                      the command "list".
                                                                      """)
    add_database_flag(analysis_parser)
    analysis_parser.add_argument('-s', '--subdocuments', action='store_true', default=False, 
                           help='Breaks a document into subdocuments in an attempt to create better topics.')
    analysis_parser.add_argument('-a', '--topic-modeling-tool', type=str, action='store', default='MalletLDA',
                                 choices=['MalletLDA'],
                                 help="""Choose the method of topic analysis, one of:
                                      MalletLDA (default) Options include number-of-topics and subdocuments.
                                      """)
    analysis_parser.add_argument('-t', '--number-of-topics', type=int, action='store', default=50, 
                           help='The number of topics that will be created.')
    
    
    analysis_parser.set_defaults(which='analyze')
    
    # list command
    list_parser = subparsers.add_parser('list', help='Lists the datasets and analyses in the database.')
    add_database_flag(list_parser)
    list_parser.set_defaults(which='list')
    
    # measure command
    measure_parser = subparsers.add_parser('measure', help='Run metrics.')
    measure_parser.add_argument('dataset_identifier', type=str, help="""\
                                                           The dataset identifier as printed at the \
                                                           end of the import command or as shown in \
                                                           the command "list".
                                                           """)
    measure_parser.add_argument('analysis_identifier', type=str, help="""\
                                                           The analysis identifier as printed at the \
                                                           end of the analyze command or as shown in \
                                                           the command "list".
                                                           """)
    add_database_flag(measure_parser)
    measure_parser.add_argument('-m', '--metrics', type=str, action='append', default=[], 
                                choices=import_utilities.get_all_metric_names(),
                                help='Specify a non-basic metric to include.')
    measure_parser.set_defaults(which='measure')
    
    # link command
    link_parser = subparsers.add_parser('link', help='Links the database to the Topical Guide server.')
    link_parser.add_argument('dataset_name', type=str, 
                             help='The dataset name or unique identifier.')
    link_parser.add_argument('database_config', type=str, 
                             help='Takes a path to a config file specifying where the database is that contains an imported dataset.')
    link_parser.set_defaults(which='link')
    
    # migrate command
    migrate_parser = subparsers.add_parser('migrate', help='A utility that migrates a dataset from one database to another database.')
    migrate_parser.add_argument('dataset_name', type=str,
                               help='The dataset name/identifier for the dataset to be moved.')
    migrate_parser.add_argument('from_database', type=str, 
                                help='The database configuration file the dataset is in, or default for the default database.')
    migrate_parser.add_argument('to_database', type=str, 
                                help='The database configuration file to move the dataset to, or default for the default database.')
    migrate_parser.set_defaults(which='migrate')
    
    # remove-metrics
    remove_metrics_parser = subparsers.add_parser('remove-metrics', help='A utility to remove metrics from a dataset.')
    remove_metrics_parser.add_argument('dataset_name', type=str, 
                                help='The dataset name/unique identifier.')
    remove_metrics_parser.add_argument('analysis_name', type=str, 
                                help='The analysis name/unique identifier.')
    add_database_flag(remove_metrics_parser)
    remove_metrics_parser.add_argument('-m', '--metrics', type=str, action='append', default=[], 
                                choices=import_utilities.get_all_metric_names(),
                                help='Specify a non-basic metric to remove, leave blank to remove all metrics.')
    remove_metrics_parser.set_defaults(which='remove-metrics')
    
    # parse arguments
    args = parser.parse_args()
    
    # execute command
    start_time = time.time()
    if args.which == 'import':
        exec_import_dataset(args)
    elif args.which == 'check':
        exec_check_dataset(args)
    elif args.which == 'analyze':
        exec_run_analysis(args)
    elif args.which == 'list':
        exec_list(args)
    elif args.which == 'measure':
        exec_run_metrics(args)
    elif args.which == 'link':
        exec_link(args)
    elif args.which == 'migrate':
        exec_migrate_dataset(args)
    elif args.which == 'remove-metrics':
        exec_remove_metrics(args)
    print('Total time taken: %s seconds'%str(datetime.timedelta(seconds=time.time() - start_time)))

# vim: et sw=4 sts=4
