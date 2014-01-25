#!/usr/bin/python
## -*- coding: utf-8 -*-

from __future__ import print_function

import os
import sys
import json
import codecs
import subprocess

from tasks.general_task import DataSetImportTask

from build import create_dirs_and_open # add this to a general toolset

#TODO eradicate dependence on the config script

#TODO eliminate doit
#~ Backend Running Sequence:
#~ 
#~ -- extract_data # done
#~ -- mallet_input # done
#~ -- dataset_import
#~ -- mallet_imported_data #done
#~ -- mallet_output_gz # next
#~ -- mallet_output #next
#~ -- analysis_import
#~ -- metadata_import:word_tokens
#~ -- metadata_import:word_types
#~ -- metadata_import:datasets
#~ -- metadata_import:documents
#~ -- metadata_import:analysis
#~ -- metadata_import:topics
#~ -- name_schemes:Top3
#~ -- dataset_metrics:counts
#~ -- analysis_metrics:entropy
#~ -- topic_metrics:word_entropy
#~ -- topic_metrics:token_count
#~ -- topic_metrics:type_count
#~ -- topic_metrics:document_entropy
#~ -- pairwise_topic_metrics:document_correlation
#~ -- pairwise_topic_metrics:word_correlation
#~ -- document_metrics:topic_entropy
#~ -- document_metrics:token_count
#~ -- document_metrics:type_count
#~ -- pairwise_document_metrics:topic_correlation
#~ .  hash_java
#~ -- compile_java
#~ -- graphs:Top3

def transfer_data(dataset, dataset_destination_dir, document_destination_dir):
    '''/
    Transfers the dataset's documents and metadata into files located on the server.
    Ex: $TOPICAL_GUIDE_ROOT/working/datasets/files
        $TOPICAL_GUIDE_ROOT/working/datasets/metadata/documents.json
    '''
        
    # copy the documents over
    dataset.copy_contents_to_directory(document_destination_dir)
    
    # copy the metadata over
    metadata_file_name = os.path.join(dataset_destination_dir, 'metadata', 'documents') + '.json'
    w = create_dirs_and_open(metadata_file_name)
    metadata = {'types':dataset.get_document_metadata_types(), \
                'data':dataset.get_all_documents_metadata()}
    w.write(json.dumps(metadata))
    w.close()

def prepare_mallet_input(dataset, dataset_destination_dir, document_destination_dir):
    '''\
    Combines every document into one large text file for processing with mallet.
    '''
    mallet_input_file = os.path.join(dataset_destination_dir, "mallet_input.txt")
    
    w = codecs.open(mallet_input_file, 'w', 'utf-8')
    count = 0
    for root, dirs, files in os.walk(document_destination_dir):
        # for each file, strip out '\n' and '\r' and put onto one line in the 
        # mallet input file
        for f in files:
            count += 1
            path = '{0}/{1}'.format(root, f)
            # the [1:] takes off a leading /
            partial_root = root.replace(document_destination_dir, '')[1:]
            if partial_root:
                mallet_path = '{0}/{1}'.format(partial_root, f)
            else:
                mallet_path = f
            text = open(path).read().decode('utf-8').strip().replace('\n',' ').replace('\r',' ')
            w.write(u'{0} all {1}'.format(mallet_path, text))
            w.write(u'\n')
        if not count:
            raise Exception('No files processed')

def run_mallet(dataset, dataset_destination_dir, document_destination_dir, topical_guide_root_dir):
    '''\
    Runs mallet; mallet performs word counts and other basic statistics.
    '''
    pass
    c = dict()
    mallet_exe = os.path.join(topical_guide_root_dir, 'tools/mallet/mallet')
    mallet_imported_data_file = os.path.join(dataset_destination_dir, 'imported_data.mallet')
    
    #TODO why is import-dir being used?
    #this means compiling data to single file is unnecessary
    cmd = '%s import-dir --input %s --output %s --keep-sequence --set-source-by-name --source-name-prefix "file:%s/%s/" --remove-stopwords' \
        % (mallet_exe, document_destination_dir, mallet_imported_data_file, \
        os.getcwd(), document_destination_dir)

    #~ if 'extra_stopwords_file' in c:
        #~ cmd += ' --extra-stopwords ' + c['extra_stopwords_file']
#~ 
    #~ if 'token_regex' in c and c['token_regex']:
        #~ cmd += " --token-regex " + c['token_regex']
    print("Running: " + cmd)
    cmd = [mallet_exe, 'import-dir', '--input', document_destination_dir, '--output',\
            mallet_imported_data_file, '--keep-sequence', '--set-source-by-name',\
            '--source-name-prefix', '"file:%s/%s/"'%(os.getcwd(), document_destination_dir),\
            '--remove-stopwords']
    subprocess.check_call(cmd, stdout=sys.stdout)

def import_dataset(dataset):
    '''\
    Imports the dataset describle by 'dataset' (which should be of type DataSetImportTask).
    '''
    # configure Django Settings
    os.environ['DJANGO_SETTINGS_MODULE'] = 'topic_modeling.settings'
    
    # print a friendly message
    print()
    print("----- Topical Guide Data Import System -----")
    print("Dataset name: " + dataset.get_dataset_readable_name())
    print("Creator: " + dataset.get_dataset_creator())
    print("Source: " + dataset.get_dataset_source())
    print()
    
    from import_tool.local_settings import LOCAL_DIR
    # dataset, document import destination
    topical_guide_root_dir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    dataset_destination_dir = os.path.join(LOCAL_DIR, 'datasets', dataset.get_dataset_name())
    if not os.path.exists(dataset_destination_dir):
        os.mkdir(dataset_destination_dir)
    document_destination_dir = os.path.join(dataset_destination_dir, 'files')
    if not os.path.exists(document_destination_dir):
        os.mkdir(document_destination_dir)
    
    
    # Move the dataset data to a stable location on the server.
    print('Copying data from dataset object...')
    transfer_data(dataset, dataset_destination_dir, document_destination_dir)
    
    # TODO either the DataSetImportTask needs to strip out punctuation, xml tags, etc.
    # TODO or we need to do it in this function
    # Generate the mallet input file.
    print('Preparing mallet input file...')
    prepare_mallet_input(dataset, dataset_destination_dir, document_destination_dir)
    
    # Run mallet
    # TODO it appears that mallet is not using the document prepared for it
    # TODO in the previous function, find out why and adjust accordingly
    print('Running mallet...')
    run_mallet(dataset.get_analysis_settings(), dataset_destination_dir, document_destination_dir, topical_guide_root_dir)
    
    
    
    raise Exception("stop")
    
    #the usual doit processes will run after this line
    # TODO delete the following after doit is stripped out
    try:
        from import_tool.local_settings import LOCAL_DIR
    except ImportError:
        raise Exception("Import error looking for local_settings.py. "
                "Look at import_tool/local_settings.py.sample for help")
    DB_BASE = os.path.join(LOCAL_DIR, '.dbs')
    if not os.path.exists(DB_BASE):
        os.mkdir(DB_BASE)
    sys.path.append("tools/doit")
    from doit.doit_cmd import cmd_main
    path = os.path.abspath('import_tool/backend.py')

    #The database file where we'll store info about this build
    db_name = os.path.join(DB_BASE, "{0}.db".format("Conference_Talks_on_Agency".replace('/','_')))

    args = ['-f', path] + ['--db', db_name]
    res = cmd_main(args)


# vim: et sw=4 sts=4
