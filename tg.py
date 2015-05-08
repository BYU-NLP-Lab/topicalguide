#!/usr/bin/env python
from __future__ import division, print_function, unicode_literals

import os
import re
from os.path import isfile, isdir, isabs, join
import argparse
import time
import datetime
from import_tool import import_system_utilities, basic_tools
from import_tool.dataset.interfaces import datasets
from import_tool.analysis.interfaces import analyses

# For example usage see the README.
# For help:
# python tg.py -h


def get_database_configurations(file_path):
    """
    Get the database configurations, an error is thrown if the \
    file cannot be read or is not found.
    If the contents don't make sense return an empty dictionary.
    For relative filenames, the folder they will be relative to is \
    the working directory.
    file_path -- file specifying the database configurations in key: value pairs.
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
        if not isabs(database_config['NAME']): # create an absolute path if a relative one is specified
            topical_guide_dir = os.path.abspath(os.path.dirname(__file__))
            database_config['NAME'] = os.path.join(topical_guide_dir, 'working', database_config['NAME'])
    
    return database_config


def get_dataset(args):
    """Read the args and return a dataset."""
    if args.dataset_class not in datasets:
        raise Exception('Invalid dataset class.')
    else:
        dataset = datasets[args.dataset_class](args.dataset, is_recursive=args.recursive)
    
    if args.identifier:
        dataset.name = args.identifier
    filters = []
    if args.remove_html_tags:
        filters.append(basic_tools.remove_html_tags)
    if args.convert_html_entities:
        filters.append(basic_tools.replace_html_entities)
    if args.dataset_class in ['MalletLDA', 'MalletHLDA']:
        dataset.add_text_filters(filters)
    
    return dataset


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
    directories = import_system_utilities.get_common_working_directories(dataset.name)
        
    # Make sure the tables exist in the database and get a database identifier.
    database_id = import_system_utilities.run_syncdb(database_info)
    # Make sure that the default database exists
    if database_id != 'default': # Check so syncdb isn't run twice in a row for no reason.
        import_system_utilities.run_syncdb(None)
    
    if args.dry_run:
        # Start the dataset check process
        import_system_utilities.check_dataset(dataset)
    else:
        # Start the import process
        dataset_name = import_system_utilities.\
            import_dataset(database_id, dataset, directories, 
            public=args.public, public_documents=args.public_documents, 
            verbose=args.verbose)


def get_analysis(args, directories):
    """Read the args and return a dataset."""
    if args.analysis_tool not in analyses:
        raise Exception('Invalid topic modeling tool.')
    else:
        analysis = analyses[args.analysis_tool](join(directories['topical_guide'], 'tools/mallet/mallet'), directories['dataset'], directories['base'])
    
    if args.identifier:
        analysis.name = args.identifier
    # must come before getting stopwords
    analysis.token_regex = args.token_regex
    if args.stopwords:
        for stopwords_file in args.stopwords:
            analysis.add_stopwords_file(stopwords_file)
    if args.subdocuments:
        analysis.set_create_subdocuments_method(basic_tools.create_subdocuments)
    analysis.num_topics = args.number_of_topics
    analysis.remove_singletons = args.remove_singletons
    analysis.find_bigrams = args.bigrams
    analysis.stem_words = args.stem_words
    
    return analysis


def exec_run_analysis(args):
    """Run an analysis on the specified dataset."""
    # Get database configurations.
    database_info = None
    if args.database_config:
        database_info = get_database_configurations(args.database_config)
    
    # Make sure the tables exist in the database and get a database identifier.
    database_id = import_system_utilities.run_syncdb(database_info)
    # Make sure that the default database exists
    if database_id != 'default': # Check so syncdb isn't run twice in a row for no reason.
        import_system_utilities.run_syncdb(None)
    
    # Get common directories.
    directories = import_system_utilities.get_common_working_directories(args.dataset_identifier)
    
    # create analysis
    analysis = get_analysis(args, directories)
    
    if args.dry_run:
        import_system_utilities.check_analysis(database_id, args.dataset_identifier, analysis, directories, verbose=args.verbose)
    else:
        # run an analysis
        analysis_identifier = import_system_utilities.run_analysis(database_id, args.dataset_identifier, analysis, directories, verbose=args.verbose)


def exec_list(args):
    """List the datasets and analyses."""
    import os
    os.environ['DJANGO_SETTINGS_MODULE'] = 'topicalguide.settings'
    from django.core.wsgi import get_wsgi_application
    application = get_wsgi_application()
    from visualize.api import LATEST_API_VERSION
    options = { 
        'datasets': '*', 'dataset_attr': ['metadata'],
        'analyses': '*', 'analysis_attr': ['metadata'],
    }
    
    datasets = LATEST_API_VERSION.query_datasets(options)
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
    database_id = import_system_utilities.run_syncdb(database_info)
    # Make sure that the default database exists
    if database_id != 'default': # Check so syncdb isn't run twice in a row for no reason.
        import_system_utilities.run_syncdb(None)
    
    database_id = import_system_utilities.run_syncdb(database_info)
    import_system_utilities.link_dataset(database_id, args.dataset_name)


def exec_run_metrics(args):
    """Run the metrics on the given thing."""
    # Get database configurations.
    database_info = None
    if args.database_config:
        database_info = get_database_configurations(args.database_config)
    
    # Make sure the tables exist in the database and get a database identifier.
    database_id = import_system_utilities.run_syncdb(database_info)
    # Make sure that the default database exists
    if database_id != 'default': # Check so syncdb isn't run twice in a row for no reason.
        import_system_utilities.run_syncdb(None)
    
    if args.metrics:
        import_system_utilities.run_metrics(database_id, args.dataset_identifier, args.analysis_identifier, set(args.metrics))


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
    import_system_utilities.make_working_dir()
    
    # make sure that both databases exist
    from_db_id = import_system_utilities.run_syncdb(from_database_config)
    to_db_id = import_system_utilities.run_syncdb(to_database_config)
    
    # run migrate
    import_system_utilities.migrate_dataset(dataset_id, from_db_id, to_db_id)


def exec_remove_metrics(args):
    """Remove listed metrics from dataset."""
    # Get database configurations.
    database_info = None
    if args.database_config:
        database_info = get_database_configurations(args.database_config)
    
    # Make sure the tables exist in the database and get a database identifier.
    database_id = import_system_utilities.run_syncdb(database_info)
    # Make sure that the default database exists
    if database_id != 'default': # Check so syncdb isn't run twice in a row for no reason.
        import_system_utilities.run_syncdb(None)
    
    import_system_utilities.remove_metrics(database_id, args.dataset_name, args.analysis_name, args.metrics)


def main():
    parser = argparse.ArgumentParser()
    
    subparsers = parser.add_subparsers(title='subcommands',
                                       help='Type -h under each subcommand for additional help.')
    
    # Add database config file option to parser.
    def add_database_flag(parser):
        parser.add_argument('-d', '--database-config', type=str, action='store', default=None, 
                            help='Uses the database configurations from the given file.')
    
    # import command
    import_parser = subparsers.add_parser('import', help='Import a dataset using a built-in class.')
    import_parser.add_argument('dataset', type=str, help='Imports the dataset from the given directory.')
    add_database_flag(import_parser)
    import_parser.add_argument('-i', '--identifier', type=str, action='store', default=None, 
                               help='A unique name to import the dataset under (e.g. state_of_the_union.)')
    import_parser.add_argument('-r', '--recursive', action='store_true', default=False, 
                               help='Recursively look for documents in the given dataset\'s "documents" directory.')
    import_parser.add_argument('--remove-html-tags', action='store_true', default=False, 
                               help='Removes html tags.')
    import_parser.add_argument('--convert-html-entities', action='store_true', default=False, 
                               help='Convert html entities to characters (e.g. &gt; converts to >).')
    import_parser.add_argument('-c', '--dataset-class', type=str, action='store', default='Generic',
                               choices=datasets.keys(),
                               help='Optionally specify the dataset class used to interface with your documents.')
    import_parser.add_argument('-v', '--verbose', action='store_true', default=False,
                               help='Display information and warnings to user.')
    import_parser.add_argument('--public', action='store_true', default=False,
                               help='Make the dataset publicly accessible.')
    import_parser.add_argument('--public-documents', action='store_true', default=False,
                               help='Make the documents publicly accessible.')
    import_parser.add_argument('--dry-run', action='store_true', default=False,
                               help='Nothing is imported into the database, a list of gathered facts about the dataset is run.')
    import_parser.set_defaults(which='import')
    
    # analysis command
    analysis_parser = subparsers.add_parser('analyze', help='Allows you to choose and run an analysis on an imported dataset. Note that the basic metrics will always be run.')
    analysis_parser.add_argument('dataset_identifier', type=str, help="""\
                                                                      The dataset identifier as printed at the \
                                                                      end of the import command or as shown in \
                                                                      the command "list".
                                                                      """)
    add_database_flag(analysis_parser)
    analysis_parser.add_argument('-a', '--analysis-tool', type=str, action='store', default='MalletLDA',
                                 choices=analyses.keys(),
                                 help="""Choose the method of topic analysis, MalletLDA is default.""")
    analysis_parser.add_argument('-t', '--number-of-topics', type=int, action='store', default=50, 
                                 help='The number of topics that will be created.')
    analysis_parser.add_argument('-i', '--identifier', type=str, action='store', default=None, 
                                 help='Optionally set the identifier for this analysis. The import system will set this if not specified.')
    analysis_parser.add_argument('-l', '--number-of-levels', type=int, action='store', default=2, 
                                 help='Used only in heirarchical topic models. The number of levels in the tree.')
    analysis_parser.add_argument('--stopwords', type=str, action='append', default=None, 
                                help='Specify a file containing a carriage return separated list of words to exclude.')
    analysis_parser.add_argument('--remove-singletons', action='store_true', default=False, 
                                help='Remove word types that occur infrequently: count <= max(1, log(|documents|) - 2).')
    analysis_parser.add_argument('--bigrams', action='store_true', default=False, 
                                help='Specify whether or not to find bigrams as a preprocessing step.')
    analysis_parser.add_argument('--subdocuments', action='store_true', default=False, 
                           help='Breaks a document into subdocuments in an attempt to create better topics.')
    analysis_parser.add_argument('--stem-words', action='store_true', default=False,
                                help="""
                                This enables basic word stemming as defined by the Porter 2 algorithm.
                                Note that you may need to build the stemmer by running the script
                                "tools/stemmer/make_english_stemmer.sh" from the directory "tools/stemmer".
                                """)
    analysis_parser.add_argument('--token-regex', type=unicode, action='store', default=import_system_utilities.TOKEN_REGEX,
                                help=
                                """Optionally specify the token regex to be used with this dataset, 
                                allowing white space will cause errors.
                                Reference the python re module for allowed regex patterns.
                                Note that re.UNICODE flag is always set.
                                """)
    analysis_parser.add_argument('-v', '--verbose', action='store_true', default=False,
                                help='Display information and warnings to user.')
    analysis_parser.add_argument('--dry-run', action='store_true', default=False,
                                help='Nothing is imported into the database, rather the analysis is run and the output is checked for errors.')
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
                                choices=import_system_utilities.get_all_metric_names(),
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
                                choices=import_system_utilities.get_all_metric_names(),
                                help='Specify a non-basic metric to remove, leave blank to remove all metrics.')
    remove_metrics_parser.set_defaults(which='remove-metrics')
    
    # parse arguments
    args = parser.parse_args()
    
    # execute command
    start_time = time.time()
    execute = {
        'import': exec_import_dataset,
        'analyze': exec_run_analysis,
        'list': exec_list,
        'measure': exec_run_metrics,
        'link': exec_link,
        'migrate': exec_migrate_dataset,
        'remove-metrics': exec_remove_metrics,
    }
    if args.which in execute:
        execute[args.which](args)
    else:
        print('That subparser isn\'t recognized.')
    print('Total time taken: %s seconds'%str(datetime.timedelta(seconds=time.time() - start_time)))

if __name__ == '__main__':
    main()

# vim: et sw=4 sts=4
