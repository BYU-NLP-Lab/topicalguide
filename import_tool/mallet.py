#!/usr/bin/python
## -*- coding: utf-8 -*-

from __future__ import print_function

# general utilities
import os
import codecs
import subprocess

# TODO figure out if this method/step is needed
# see comments in run_mallet() for details
def prepare_mallet_input(dataset_dir, document_dir):
    '''\
    Combines every document into one large text file for processing with mallet.
    '''
    mallet_input_file = os.path.join(dataset_dir, "mallet_input.txt")
    
    w = codecs.open(mallet_input_file, 'w', 'utf-8')
    count = 0
    for root, dirs, files in os.walk(document_dir):
        # for each file/document, strip out '\n' and '\r' and put onto one line in the 
        # mallet input file
        for f in files:
            count += 1
            path = '{0}/{1}'.format(root, f)
            # the [1:] takes off a leading /
            partial_root = root.replace(document_dir, '')[1:]
            if partial_root:
                mallet_path = '{0}/{1}'.format(partial_root, f)
            else:
                mallet_path = f
            text = open(path).read().decode('utf-8').strip().replace('\n',' ').replace('\r',' ')
            w.write(u'{0} all {1}'.format(mallet_path, text))
            w.write(u'\n')
        if not count:
            raise Exception('No files processed')

def run_mallet(analysis_settings, dataset_dir, document_dir, topical_guide_dir):
    '''\
    Runs mallet; mallet performs word counts and other basic statistics.
    '''
    c = analysis_settings.get_mallet_configurations(topical_guide_dir, dataset_dir)

    
        
    #TODO why is import-dir being used?
    #this means compiling data to single file is unnecessary
    #since mallet will pull data from each of the files in the specified directory
    print('  Running "mallet import-file..."')
    if not os.path.exists(c['mallet_imported_data']):
        cmd = [c['mallet'], 'import-file', 
               '--input', c['mallet_input'], 
               '--output', c['mallet_imported_data'], 
               '--keep-sequence', 
               '--set-source-by-name',
               # TODO do we need this? I don't think so
               #'--source-name-prefix', '"file:%s/%s/"'%(os.getcwd(), document_dir),
               '--remove-stopwords']
        #TODO add methods to get any specified settings for the below options
        #~ if 'extra_stopwords_file' in c:
            #~ cmd += ' --extra-stopwords ' + c['extra_stopwords_file']
        #~ if 'token_regex' in c and c['token_regex']:
            #~ cmd += " --token-regex " + c['token_regex']
        try:
            subprocess.check_call(cmd)
        except Exception as e:
            # clean up before propagating the Exception
            cmd = 'rm -f %s' % c['mallet_imported_data']
            subprocess.check_call(cmd, shell=True)
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
            cmd = 'rm -f %s' % c['mallet_output_gz']
            subprocess.check_call(cmd, shell=True)
            cmd = 'rm -f %s' % c['mallet_doctopics_output']
            subprocess.check_call(cmd, shell=True)
            raise e
    
    print('  Extracting mallet output...')
    if not os.path.exists(c['mallet_output']):
        cmd = 'gunzip -c %s > %s' % (c['mallet_output_gz'], c['mallet_output'])
        try:
            subprocess.check_call(cmd, shell=True)
        except Exception as e:
            cmd = 'rm -f %s' % c['mallet_output']
            subprocess.check_call(cmd, shell=True)
            raise e

# vim: et sw=4 sts=4
