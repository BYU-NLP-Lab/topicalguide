#!/usr/bin/env python

from __future__ import print_function

import os
import sys
import argparse

from import_tool.dataset_classes.generic_dataset \
    import GenericDataset, GenericTools, AnalysisSettings


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
        database_config = GenericTools.metadata_to_dict(f.read()) # read in the database configurations
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
        

def exec_check_dataset(args):
    """
    Check the dataset for blank documents and tell you what metadata types you have.
    """
    dataset = GenericDataset(args.dataset)
    
    blank_documents = []
    blank_metadata = []
    metadata_types = {}
    arg = {'blank_documents': blank_documents, 'blank_metadata': blank_metadata, 
            'metadata_types': metadata_types}
    def check_document(arg, doc):
        content = doc.get_content()
        meta = doc.get_metadata()
        if content == '' or content == None: # collect blank documents
            arg['blank_documents'].append(path)
        if meta == {} or meta == None: # collect blank metadata
            arg['blank_metadata'].append(path)
        else: # collect metadata types
            GenericTools.collect_types(arg['metadata_types'], meta)
            
    GenericTools.walk_documents(dataset, check_document, arg)
    
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
    GenericTools.collect_types(dataset_metadata_types, dataset.get_metadata())
    
    print('Dataset readable name: ')
    print('"' + dataset.get_readable_name() + '"')
    print()
    
    print('Dataset description: ')
    print('"' + dataset.get_description() + '"')
    print()
    
    if dataset_metadata_types:
        print('Listing of dataset metadata and their associated types: ')
        for key, value in dataset_metadata_types.items():
            print(key + ': ' + value)
        print()
    else:
        print('No dataset metadata.')
    
    if metadata_types:
        print('Listing of document metadata and their associated types: ')
        for key, value in metadata_types.items():
            print(key + ': ' + value)
        print()
    else:
        print('No document metdata')

def exec_import_generic_dataset(args):
    """
    Perform basic checks and create necessary objects in preparation to import.
    Import dataset into database.
    Run the analysis and import results into the database.
    Run metrics and import results into the database.
    Return nothing.
    """
    from import_tool import import_utilities
    
    # create GenericDataset object and set settings
    dataset_object = GenericDataset(args.dataset)
    dataset_object.set_is_recursive(args.recursive)
    dataset_object.set_has_subdocuments(args.subdocuments)
    if args.identifier:
        dataset_object.set_identifier(args.identifier)
    
    # create analysis settings
    analysis_settings = AnalysisSettings()
    if args.number_of_topics:
        if args.number_of_topics > 0:
            analysis_settings.set_number_of_topics(args.number_of_topics)
        else:
            raise Exception('Number of topics is non-positive.')
    
    # get database configurations
    database_info = None
    if args.database_config:
        database_info = get_database_configurations(args.database_config)
    
    # get common directories
    directories = import_utilities.get_common_working_directories(dataset_object.get_identifier())
    
    # make sure the tables exist in the database and get an identifier
    database_id = import_utilities.run_syncdb(database_info)
    
    # make sure that the default database exists
    if database_id != 'default':
        import_utilities.run_syncdb(None)
    
    # start the import process
    import_utilities.import_dataset(database_id, dataset_object, 
                                    directories['dataset'], 
                                    directories['documents'])
    
    # link dataset to default database
    import_utilities.link_dataset(database_id, dataset_object.get_identifier())
    
    # run an analysis
    import_utilities.run_analysis(database_id, dataset_object, 
                                  analysis_settings, 
                                  directories['topical_guide'], 
                                  directories['dataset'],
                                  directories['documents'])
    
    # run metrics on an analysis
    import_utilities.run_basic_metrics(database_id, dataset_object, analysis_settings)


def exec_link(args):
    """Link a dataset to the default database."""
    # get database configurations
    if args.dataset_name and args.database_config:
        database_info = get_database_configurations(args.database_config)
        database_id = import_utilities.run_syncdb(database_info)
        import_utilities.link_dataset(database_id, args.dataset_name)
    else:
        print('You need to specify a dataset name and a database configuration file.')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    
    subparsers = parser.add_subparsers(title='subcommands',
                                       help='Type -h under each subcommand for additional help.')
    
    # import command
    import_parser = subparsers.add_parser('import', help='Import a dataset using a built-in class.')
    import_parser.add_argument('dataset', type=str,
                               help='Imports the dataset from the given directory.')
    import_parser.add_argument('-d', '--database-config', type=str, action='store', default=None, 
                               help='Uses the database configurations from the given file.')
    import_parser.add_argument('-i', '--identifier', type=str, action='store', default=None, 
                               help='A unique name to import the dataset under (e.g. state_of_the_union.)')
    import_parser.add_argument('-r', '--recursive', action='store_true', default=False, 
                               help='Recursively look for documents in the given dataset directory.')
    import_parser.add_argument('-s', '--subdocuments', action='store_true', default=False, 
                               help='Breaks a document into subdocuments to create better topics.')
    import_parser.add_argument('-t', '--number-of-topics', type=int, action='store', default=None, 
                               help='The number of topics that will be created.')
    import_parser.set_defaults(which='import')
    
    # link command
    link_parser = subparsers.add_parser('link', help='Links the database to the Topical Guide server.')
    link_parser.add_argument('dataset-name', type=str, default=None, 
                             help='The dataset name or unique identifier.')
    link_parser.add_argument('database-config', type=str, default=None, 
                             help='Takes a path to a config file specifying where the database is that contains an imported dataset.')
    link_parser.set_defaults(which='link')
    
    # check command
    check_parser = subparsers.add_parser('check', help='A utility that helps check the integrity of documents and metadata raising red flags if inconsistencies are found among the metadata keys or if there are any blank documents.')
    check_parser.add_argument('dataset', type=str,
                               help="""\
                                    The dataset to be checked for missing metadata, \
                                    missing content, and prints info about the metadata \
                                    types of the documents to aid in importing.
                                    """)
    check_parser.set_defaults(which='check')
    
    args = parser.parse_args()
    
    if args.which == 'import':
        exec_import_generic_dataset(args)
    elif args.which == 'link':
        exec_link(args)
    elif args.which == 'check':
        exec_check_dataset(args)

# vim: et sw=4 sts=4
