#!/usr/bin/python
## -*- coding: utf-8 -*-

from __future__ import print_function

# general utilities
import os
import codecs
import subprocess
import json


def prepare_mallet_input(analysis_settings, dataset_dir, document_dir):
    """
    Combine every document into one large text file for processing with mallet.
    """
    mallet_input_file = os.path.join(dataset_dir, 'mallet_input.txt')
    subdoc_to_doc_map_file = os.path.join(dataset_dir, 'subdoc_to_doc_map.json')
    subdoc_to_doc_map = {}
    
    if os.path.exists(mallet_input_file) and os.path.exists(subdoc_to_doc_map_file):
        return
    
    with codecs.open(mallet_input_file, 'w', 'utf-8') as w:
        count = 0
        for root, dirs, file_names in os.walk(document_dir):
            # for each file/document, strip out '\n' and '\r' and put 
            # onto one line in the mallet input file
            for file_name in file_names:
                count += 1
                path = '{0}/{1}'.format(root, file_name)
                # the [1:] takes off a leading /
                partial_root = root.replace(document_dir, '')[1:]
                if partial_root:
                    mallet_path = '{0}/{1}'.format(partial_root, file_name)
                else:
                    mallet_path = file_name
                # read file and split into subdocuments if specified
                with codecs.open(path) as f:
                    content = unicode(f.read(), errors='ignore')
                    subdocuments = analysis_settings.create_subdocuments(file_name, content)
                    for subdoc in subdocuments:
                        subdoc_to_doc_map[subdoc[0]] = mallet_path
                        text = subdoc[1].replace(u'\n', u' ').replace(u'\r', u' ')
                        w.write(u'{0} all {1}\n'.format(subdoc[0], analysis_settings.filter_text(text)))
            if not count:
                raise Exception('No files processed.')
    # record which subdocuments belong to which documents
    with codecs.open(subdoc_to_doc_map_file, 'w', 'utf-8') as w:
        w.write(json.dumps(subdoc_to_doc_map))

def run_mallet(analysis_settings, dataset_dir, document_dir, topical_guide_dir):
    """
    Run mallet.
    """
    analysis_settings.save_stopwords(os.path.join(dataset_dir, 'stopwords.txt'))
    c = analysis_settings.get_mallet_configurations(topical_guide_dir, dataset_dir)
    
    print('  Running "mallet import-file..."')
    if not os.path.exists(c['mallet_imported_data']):
        cmd = [c['mallet'], 'import-file', 
               '--input', c['mallet_input'], 
               '--output', c['mallet_imported_data'], 
               '--keep-sequence', 
               '--set-source-by-name',
               '--remove-stopwords']
        
        if 'extra_stopwords_file' in c and c['extra_stopwords_file']:
            cmd.append(' --extra-stopwords ')
            cmd.append(c['extra_stopwords_file'])
        
        if 'token_regex' in c and c['token_regex']:
            cmd.append(' --token-regex ')
            cmd.append(c['token_regex'])
        
        try:
            subprocess.check_call(cmd)
        except Exception as e:
            os.remove(c['mallet_imported_data'])
            raise e
    
    print('  Running "mallet train-topics..."')
    if not (os.path.exists(c['mallet_output_gz']) and os.path.exists(c['mallet_doctopics_output'])):
        cmd = [c['mallet'], 'train-topics', 
               '--input', c['mallet_imported_data'],
               '--optimize-interval', '%s' % c['mallet_optimize_interval'],
               '--num-iterations', '%s' % c['num_iterations'], 
               '--num-topics', '%s' % c['num_topics'],
               '--output-state', c['mallet_output_gz'], 
               '--output-doc-topics', c['mallet_doctopics_output']]
        try:
            subprocess.check_call(cmd)
        except Exception as e:
            os.remove(c['mallet_output_gz'])
            os.remove(c['mallet_doctopics_output'])
            raise e
    
    print('  Extracting mallet output...')
    if not os.path.exists(c['mallet_output']):
        cmd = 'gunzip -c %s > %s' % (c['mallet_output_gz'], c['mallet_output'])
        try:
            subprocess.check_call(cmd, shell=True)
        except Exception as e:
            os.remove(c['mallet_output'])
            raise e

# vim: et sw=4 sts=4
