#!/usr/bin/env python

from __future__ import print_function

import os
import sys
import argparse



# Example usage:
# ./topicalguide.py import /local/cj264/topicalguide/raw-data/agency_conference_talks/

# For help:
# ./topicalguide.py -h

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    
    subparsers = parser.add_subparsers(title='subcommands',
                                       help='Type -h under each subcommand for additional help.')
    
    import_parser = subparsers.add_parser('import', help='Import a dataset using a built-in class.')
    import_parser.add_argument('dataset', type=str,
                               help='Imports the dataset from the given folder.')
    import_parser.add_argument('-r', '--recursive', action='store_true',
                               help='Recursively looks for documents in the given dataset folder.')
    import_parser.add_argument('-s', '--subdocuments', action='store_true',
                               help='Breaks a document into subdocuments to create better topics.')
    import_parser.set_defaults(which='import')
    
    import_parser = subparsers.add_parser('link', help='Takes a path to a database containing an imported dataset.')
    import_parser.add_argument('database', type=str,
                               help='Links the database to the Topical Guide server.')
    import_parser.set_defaults(which='link')
    
    import_parser = subparsers.add_parser('check', help='A utility that helps check the integrity of documents and metadata raising red flags if inconsistencies are found amoung the metadata keys or if there are any blank documents.')
    import_parser.add_argument('dataset', type=str,
                               help='The dataset to be checked for inconsistencies.')
    import_parser.set_defaults(which='check')
    
    server_parser = subparsers.add_parser('server')
    server_parser.add_argument('command', type=str, choices=['start'],
                               help='Starts the Topical Guide server.')
    server_parser.set_defaults(which='server')
    
    args = parser.parse_args()
    
    if args.which == 'import':
        from import_tool import import_dataset
        from import_tool.dataset_classes.generic_dataset import DataSetImportTask
        
        if os.path.isdir(args.dataset):
            dataset_object = DataSetImportTask(args.dataset)
            import_dataset.import_dataset(dataset_object)
        else:
            print('Not a valid dataset path.')
    elif args.which == 'link':
        print('Not yet implemented.')
    elif args.which == 'check':
        print('Not yet implemented.')
    elif args.which == 'server':
        print('Not yet implemented.')

# vim: et sw=4 sts=4
