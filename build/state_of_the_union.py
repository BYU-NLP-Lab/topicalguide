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

#State of the Union Addresses Dataset build settings
import os
from build.state_of_the_union.extract_sotua_documents import extract_state_of_the_union
from build.state_of_the_union.generate_attributes_file import generate_attributes_file

from backend import c

def initialize_config(config):
    config['num_topics'] = 100
    config['chron_list_filename'] = 'chronological_list.wiki'
    config['addresses_filename'] = 'state_of_the_union_addresses.txt'
    config['dataset_name'] = 'state_of_the_union'
    config['dataset_readable_name'] = 'State of the Union Addresses 1790-2010'
    config['dataset_description'] = \
    '''State of the Union Addresses taken from WikiSource by adding all
     addresses to a "book" and downloading it. Created by Josh Hansen.'''
    config['suppress_default_document_metadata_task'] = True
    config['metadata_filenames'] = lambda c: {
          'datasets': '%s/datasets.json' % c['raw_data_dir']
    }

def task_document_metadata():
    doc_meta_filename = c['metadata_filenames']['documents']
    task = dict()
    task['targets'] = [doc_meta_filename]
    task['actions'] = [(generate_attributes_file,
                ['%s/%s' % (c['raw_data_dir'], c['chron_list_filename']), doc_meta_filename])]
    task['clean'] = ['rm -f '+doc_meta_filename]
    return task

def task_extract_data():
    def utd(_task, _vals): return os.path.exists(c['files_dir'])
        
    task = dict()
    task['targets'] = [c['files_dir']]
    task['actions'] = [
        (extract_state_of_the_union,
         ['%s/%s' % (c['raw_data_dir'], c['chron_list_filename']),
          '%s/%s' % (c['raw_data_dir'], c['addresses_filename']),
          c['files_dir']]
        )
    ]
    task['clean'] = ['rm -rf '+c['files_dir']]
    task['uptodate'] = [utd]
    return task
