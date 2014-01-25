#!/usr/bin/env python

from __future__ import print_function

import os
import sys
import argparse

from import_tool import import_dataset
from import_tool.tasks.general_task import DataSetImportTask

# Example usage:
# ./topicalguide.py import /local/cj264/topicalguide/raw-data/agency_conference_talks/

# For help:
# ./topicalguide.py -h

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    
    subparsers = parser.add_subparsers(title='subcommands',
                                       description='valid subcommands',
                                       help='Type -h under each subcommand for additional help.')
    
    import_parser = subparsers.add_parser('import')
    import_parser.add_argument('dataset', type=str,
                               help='Imports the dataset from the given folder.')
    import_parser.add_argument('-r', '--recursive', action='store_true',
                               help='Recursively looks for documents in the given dataset folder.')
    import_parser.set_defaults(which='import')
    
    server_parser = subparsers.add_parser('server')
    server_parser.add_argument('command', type=str, choices=['start'],
                               help='Starts the server.')
    server_parser.set_defaults(which='server')
    
    args = parser.parse_args()
    
    if args.which == 'import':
        if os.path.isdir(args.dataset):
            import_dataset.import_dataset(DataSetImportTask(args.dataset))
        else:
            print('Not a valid dataset path.')
    elif args.which == 'server':
        print('Start server functionality not yet implemented.')

# vim: et sw=4 sts=4
