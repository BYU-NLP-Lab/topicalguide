#!/usr/bin/env python

from __future__ import print_function

import os
import sys
import argparse
import time

from import_tool import import_utilities
from import_tool import basic_tools
from import_tool.dataset_scripts.generic_dataset import GenericDataset
from import_tool.dataset_scripts.json_dataset import JsonDataset
from import_tool.dataset_scripts.wikipedia_dataset import WikipediaDataset
from import_tool.analysis_scripts.mallet_analysis import MALLETAnalysis

# Example usage:
# ./topicalguide.py import raw-data/agency_conference_talks/
# ./topicalguide.py import raw-data/agency_conference_talks/ -d raw-data/agency_conference_talks/database_config.txt

# For help:
# ./topicalguide.py -h


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
    if 'NAME' in database_config and not os.path.isdir(database_config['NAME']):
        if not os.path.isabs(database_config['NAME']): # create an absolute path if a relative one is specified
            topical_guide_dir = os.path.abspath(os.path.dirname(__file__))
            database_config['NAME'] = os.path.join(topical_guide_dir, 'working', database_config['NAME'])
    
    return database_config
        
def get_dataset(args):
    """Read the args and return a dataset."""
    if args.which in ('import', 'check'):
        dataset = GenericDataset(args.dataset)
        dataset.set_is_recursive(args.recursive)
        if args.identifier:
            dataset.set_identifier(args.identifier)
    elif args.which in ('import-json', 'check-json'):
        dataset = JsonDataset(args.dataset)
        dataset.set_is_recursive(args.recursive)
        if args.identifier:
            dataset.set_identifier(args.identifier)
    else:
        raise Exception('Invalid selection.')
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
    # get database configurations
    database_info = None
    if args.database_config:
        database_info = get_database_configurations(args.database_config)
    
    # create GenericDataset object and set settings
    dataset = get_dataset(args)
    
    # get common directories
    directories = import_utilities.get_common_working_directories(dataset.get_identifier())
    
    # create analysis
    if args.number_of_topics:
        analysis = MALLETAnalysis(directories['topical_guide'], directories['dataset'], args.number_of_topics)
    else:
        analysis = MALLETAnalysis(directories['topical_guide'], directories['dataset'])
    if args.filters:
        with open(args.filters, 'r') as f:
            lines = f.readlines()
            filters = [line.strip() for line in lines]
            analysis.add_filters(filters)
            dataset.add_filters(filters)
    if args.subdocuments:
        analysis.set_create_subdocuments_method(basic_tools.create_subdocuments)
    
    # make sure the tables exist in the database and get an identifier
    database_id = import_utilities.run_syncdb(database_info)
    # make sure that the default database exists
    if database_id != 'default': # check so syncdb isn't run twice in a row for no reason
        import_utilities.run_syncdb(None)
    
    # start the import process
    dataset_name = import_utilities.import_dataset(database_id, dataset, directories)
    
    # run an analysis
    analysis_name = import_utilities.run_analysis(database_id, dataset_name, analysis, directories)
    
    # run metrics on the analysis
    import_utilities.run_basic_metrics(database_id, dataset_name, analysis_name)
    if args.metrics:
        import_utilities.run_metrics(database_id, dataset_name, analysis_name, set(args.metrics))

def exec_import_wikipedia_dataset(args):
    """Import a dataset from Wikipedia.org."""
    pass

def exec_link(args):
    """Link a dataset to the default database."""
    database_info = get_database_configurations(args.database_config)
    database_id = import_utilities.run_syncdb(database_info)
    import_utilities.link_dataset(database_id, args.dataset_name)

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
    dataset_name = args.dataset_name
    analysis_name = args.analysis_name
    
    database = args.database
    database_config = None
    if database != 'default':
        database_config = get_database_configurations(database)
    
    database_id = import_utilities.run_syncdb(database_config)
    
    import_utilities.remove_metrics(database_id, dataset_name, analysis_name, args.metrics)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    
    subparsers = parser.add_subparsers(title='subcommands',
                                       help='Type -h under each subcommand for additional help.')
    
    def add_standard_flags(parser):
        parser.add_argument('-d', '--database-config', type=str, action='store', default=None, 
                            help='Uses the database configurations from the given file.')
        parser.add_argument('-i', '--identifier', type=str, action='store', default=None, 
                            help='A unique name to import the dataset under (e.g. state_of_the_union.)')
        parser.add_argument('-r', '--recursive', action='store_true', default=False, 
                            help='Recursively look for documents in the given dataset directory.')
        parser.add_argument('-s', '--subdocuments', action='store_true', default=False, 
                            help='Breaks a document into subdocuments in an attempt to create better topics.')
        parser.add_argument('-t', '--number-of-topics', type=int, action='store', default=None, 
                            help='The number of topics that will be created.')
        parser.add_argument('-m', '--metrics', type=str, action='append', default=[], 
                            choices=import_utilities.get_all_metric_names(),
                            help='Specify a non-basic metric to include.')
        parser.add_argument('-f', '--filters', type=str, action='store', default=None, 
                            help='Specify a file containing a list of the filters to apply.')
    
    # import command
    import_parser = subparsers.add_parser('import', help='Import a dataset using a built-in class.')
    import_parser.add_argument('dataset', type=str, help='Imports the dataset from the given directory.')
    add_standard_flags(import_parser)
    import_parser.set_defaults(which='import')
    
    # import-json command
    import_json_parser = subparsers.add_parser('import-json', help='Import a dataset in JSON format using a built-in class.')
    import_json_parser.add_argument('dataset', type=str, help='Imports the dataset in JSON format from the given directory.')
    add_standard_flags(import_json_parser)
    import_json_parser.set_defaults(which='import-json')
    
    # import-wikipedia command
    import_wiki_parser = subparsers.add_parser('import-wikipedia', help='Import a dataset from Wikipedia.org.')
    import_wiki_parser.add_argument('page_title', type=str, help='Imports the dataset from the given directory.')
    add_standard_flags(import_wiki_parser)
    import_wiki_parser.set_defaults(which='import-wikipedia')
    
    # link command
    link_parser = subparsers.add_parser('link', help='Links the database to the Topical Guide server.')
    link_parser.add_argument('dataset_name', type=str, 
                             help='The dataset name or unique identifier.')
    link_parser.add_argument('database_config', type=str, 
                             help='Takes a path to a config file specifying where the database is that contains an imported dataset.')
    link_parser.set_defaults(which='link')
    
    # check command
    check_parser = subparsers.add_parser('check', help='A utility that helps check the integrity of documents and metadata raising red flags if inconsistencies are found among the metadata keys or if there are any blank documents.')
    check_parser.add_argument('dataset', type=str, help="""\
                                                        The dataset to be checked for missing metadata, \
                                                        missing content, and prints info about the metadata \
                                                        types of the documents to aid in importing.
                                                        """)
    add_standard_flags(check_parser)
    check_parser.set_defaults(which='check')
    
    # check-json command
    check_json_parser = subparsers.add_parser('check-json', help='A utility that helps check the integrity of documents and metadata raising red flags if inconsistencies are found among the metadata keys or if there are any blank documents.')
    check_json_parser.add_argument('dataset', type=str, help="""\
                                                        The dataset to be checked for missing metadata, \
                                                        missing content, and prints info about the metadata \
                                                        types of the documents to aid in importing.
                                                        """)
    add_standard_flags(check_json_parser)
    check_json_parser.set_defaults(which='check-json')
    
    # check-wikipedia command
    check_wiki_parser = subparsers.add_parser('check-wikipedia', help='A utility that helps check the integrity of documents and metadata raising red flags if inconsistencies are found among the metadata keys or if there are any blank documents.')
    check_wiki_parser.add_argument('page_title', type=str, help="""\
                                                        The dataset to be checked for missing metadata, \
                                                        missing content, and prints info about the metadata \
                                                        types of the documents to aid in importing.
                                                        """)
    add_standard_flags(check_wiki_parser)
    check_wiki_parser.set_defaults(which='check-wikipedia')
    
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
    remove_metrics_parser.add_argument('database', type=str, 
                                help='The database configuration file the dataset is in, or default for the default database.')
    remove_metrics_parser.add_argument('-m', '--metrics', type=str, action='append', default=[], 
                                choices=import_utilities.get_all_metric_names(),
                                help='Specify a non-basic metric to include.')
    remove_metrics_parser.set_defaults(which='remove-metrics')
    
    # parse arguments
    args = parser.parse_args()
    
    # execute command
    start_time = time.time()
    if args.which in ('import', 'import-json', 'import-wikipedia'):
        exec_import_dataset(args)
    elif args.which == 'link':
        exec_link(args)
    elif args.which in ('check', 'check-json', 'check-wikipedia'):
        exec_check_dataset(args)
    elif args.which == 'migrate':
        exec_migrate_dataset(args)
    elif args.which == 'remove-metrics':
        exec_remove_metrics(args)
    print('Total time taken: %s seconds'%str(time.time() - start_time))

# vim: et sw=4 sts=4
