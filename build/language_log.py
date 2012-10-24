# The Topical Guide
# Copyright 2010-2011 Brigham Young University
#
# This file is part of the Topical Guide <http://nlp.cs.byu.edu/topic_browser>.
#
# The Topical Guide is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published by the
# Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# The Topical Guide is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public License
# for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with the Topical Guide.  If not, see <http://www.gnu.org/licenses/>.
#
# If you have inquiries regarding any further use of the Topical Guide, please
# contact the Copyright Licensing Office, Brigham Young University, 3760 HBLL,
# Provo, UT 84602, (801) 422-9339 or 422-3821, e-mail copyright@byu.edu.

from backend import config as c
from build import create_dirs_and_open
from nltk.tokenize.treebank import TreebankWordTokenizer
from topic_modeling import anyjson
import os, sys

c['num_topics'] = 100
c['dataset_name'] = 'language_log'
c['dataset_readable_name'] = 'Language Log'
c['suppress_default_document_metadata_task'] = True
c['raw_data_base_dir'] = '/local/jared/raw-data'
c['pairwise_document_metrics'] = [] # far too many documents

def task_extract_data():
    dest_dir = c['files_dir']
    metadata_filename = c['metadata_filenames']['documents']
    raw_data_dir = c['raw_data_dir']
    print 'looking in', raw_data_dir
    
    task = {}
    task['targets'] = [dest_dir, metadata_filename]
    task['actions'] = [(_extract, [dest_dir, metadata_filename, raw_data_dir])]
    task['clean'] = ['rm -rf {} {}'.format(dest_dir, metadata_filename)]

    def utd(_task, _vals):
        print>>sys.stderr, dest_dir, metadata_filename
        # fail
        return len(os.listdir(dest_dir)) > 0 and os.path.exists(metadata_filename)

    task['uptodate'] = [utd]
    return task

_tokenizer = TreebankWordTokenizer()

def _extract(dest_dir, metadata_filename, raw_data):
    metadata = {}
    all_files = []
    for root, _, files in os.walk(raw_data):
        for filename in files:
            if filename.endswith('.txt'):
                all_files.append([root, filename])
    num_files = len(all_files)
    print>>sys.stderr, "Extracting %d files" % num_files
    for i, (root, filename) in enumerate(all_files):
        if i % 50 == 0:
            print>>sys.stderr, ".",
            sys.stderr.flush()
        if i % 1000 == 0:
            print>>sys.stderr, ": %d%% done (%d of %d)" % (i*100//num_files, i, num_files), root, filename, dest_dir
        
        _extract_doc(root, os.path.relpath(root, raw_data), filename, dest_dir)
        meta_name = os.path.join(root, filename[:-len('.txt')] + '.meta')
        metadata[filename] = {
                'dirname': root,
                'title': filename,
                'date': open(meta_name).read()
            }
    print>>sys.stderr, "Done Extracting"
    _write_metadata(metadata, metadata_filename)

def _extract_doc(root, rel_root, filename, dest_dir):
    raw_text = open(os.path.join(root, filename)).read()
    try:
        raw_text = raw_text.decode('cp1252')
    except Exception as e:
        try:
            raw_text = raw_text.decode('utf8')
        except Exception as e:
            print filename, root, e
            print [raw_text[1500:1520]]
            raise Exception('yup, encoding fail')

    tokens = _tokenizer.tokenize(raw_text)
    out_text = ' '.join(tokens)
    out_file = create_dirs_and_open(os.path.join(dest_dir, rel_root, filename))
    try:
        out_file.write(out_text)
    except Exception as e:
        print "Failed?", e, out_file, rel_root, filename
        raise e
    out_file.close()

def _write_metadata(data, filename):
    types = {'dirname': 'text',
             'title': 'text',
             'date': 'text'
            }
    metadata_file = create_dirs_and_open(filename)
    metadata_file.write(anyjson.serialize({'types': types, 'data': data}))
    metadata_file.close()

