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


def verify_generic_dataset_path(dataset_dir):
    '''\
    Verifies that the needed files are present.
    '''
    if not os.path.isdir(dataset_dir):
        print('Invalid dataset directory.')
        exit(1)
    
    meta_path = os.path.join(dataset_dir, 'dataset_metadata.txt')
    if not (os.path.exists(meta_path) and os.path.isfile(meta_path)):
        print('The "dataset_metadata.txt" file must exist.')
        exit(1)
    
    documents_dir = os.path.join(dataset_dir, 'documents')
    if not (os.path.exists(documents_dir) and os.path.isdir(documents_dir)):
        print('The "documents" directory must exist.')
        exit(1)


def get_database_configurations(file_path):
    '''\
    Gets the database configurations, an error is thrown if the \
    file cannot be read or is not found.
    If the contents don't make sense an empty dictionary is returned.
    For relative filenames, the folder they will be relative to is \
    the working directory.
    '''
    database_config = {}
    
    key_names = ['ENGINE', 'NAME', 'HOST', 'OPTIONS', 'PASSWORD', 'PORT', 'USER']
    with open(file_path, 'r') as f:
        database_config = GenericTools.metadata_to_dict(f.read()) # read in the database configurations
    for key in key_names:
        if key.lower() in database_config: # make sure the key names are upper case
            database_config[key] = database_config[key.lower()]
            del database_config[key.lower()]
    if 'NAME' in database_config and not os.path.isdir(database_config['NAME']):
        if not os.path.isabs(database_config['NAME']): # create an absolute path if a relative one is specified
            topical_guide_dir = os.path.abspath(os.path.dirname(__file__))
            database_config['NAME'] = os.path.join(topical_guide_dir, 'working', database_config['NAME'])
    
    return database_config
        

def exec_check_dataset(args):
    '''\
    Checks the dataset for blank documents and tells you what metadata types you have.
    '''
    dataset_dir = args.dataset
    verify_generic_dataset_path(dataset_dir)
    
    
    dataset = GenericDataset(dataset_dir)
    
    blank_documents = []
    blank_metadata = []
    metadata_types = {}
    arg = {'blank_documents': blank_documents, 'blank_metadata': blank_metadata, 
            'metadata_types': metadata_types}
    def check_document(arg, identifier, path, meta, content):
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
    
    if dataset_metadata_types:
        print('Listing of dataset metadata and their associated types: ')
        for key, value in dataset_metadata_types.items():
            print(key + ': ' + value)
        print()
    
    if metadata_types:
        print('Listing of document metadata and their associated types: ')
        for key, value in metadata_types.items():
            print(key + ': ' + value)
        print()

def exec_import_generic_dataset(args):
    '''\
    Performs basic checks and creates necessary objects in preparation to import.
    '''
    verify_generic_dataset_path(args.dataset)
    
    from import_tool import import_dataset
    
    dataset_object = GenericDataset(args.dataset)
    dataset_object.set_is_recursive(args.recursive)
    dataset_object.set_has_subdocuments(args.subdocuments)
    if args.identifier:
        dataset_object.set_identifier(args.identifier)
    
    analysis_settings = AnalysisSettings()
    
    working_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'working'))
    database_file = os.path.join(working_dir, dataset_object.get_identifier() + '.sqlite3')
    
    database_info = None
    if args.database_config:
        database_info = get_database_configurations(args.database_config)
    
    import_dataset.import_dataset(dataset_object, analysis_settings, database_info)



if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    
    subparsers = parser.add_subparsers(title='subcommands',
                                       help='Type -h under each subcommand for additional help.')
    
    # import command
    import_parser = subparsers.add_parser('import', help='Import a dataset using a built-in class.')
    import_parser.add_argument('dataset', type=str,
                               help='Imports the dataset from the given directory.')
    import_parser.add_argument('-d', '--database-config', type=str,
                               help='Uses the database configurations from the given file.')
    import_parser.add_argument('--identifier', type=str, action='store', default=None, 
                               help='A unique name to import the dataset under (e.g. state_of_the_union.)')
    import_parser.add_argument('-r', '--recursive', action='store_true',
                               help='Recursively look for documents in the given dataset directory.')
    import_parser.add_argument('-s', '--subdocuments', action='store_true',
                               help='Breaks a document into subdocuments to create better topics.')
    import_parser.set_defaults(which='import')
    
    # link command
    link_parser = subparsers.add_parser('link', help='Links the database to the Topical Guide server.')
    link_parser.add_argument('database-config', type=str,
                               help='Takes a path to a config file specifying where the database is that contains an imported dataset.')
    link_parser.set_defaults(which='link')
    
    # check command
    check_parser = subparsers.add_parser('check', help='A utility that helps check the integrity of documents and metadata raising red flags if inconsistencies are found among the metadata keys or if there are any blank documents.')
    check_parser.add_argument('dataset', type=str,
                               help='''\
                                    The dataset to be checked for missing metadata, \
                                    missing content, and prints info about the metadata \
                                    types of the documents to aid in importing.
                                    ''')
    check_parser.set_defaults(which='check')
    
    args = parser.parse_args()
    
    if args.which == 'import':
        exec_import_generic_dataset(args)
    elif args.which == 'link':
        print('Not yet implemented.')
    elif args.which == 'check':
        exec_check_dataset(args)

# vim: et sw=4 sts=4
