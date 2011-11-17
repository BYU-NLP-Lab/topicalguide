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

num_topics = 100
chron_list_filename = 'chronological_list.wiki'
addresses_filename = 'state_of_the_union_addresses.txt'
dataset_name = 'state_of_the_union'
dataset_readable_name = 'State of the Union Addresses 1790-2010'
dataset_description = \
'''State of the Union Addresses taken from WikiSource by adding all
 addresses to a "book" and downloading it. Created by Josh Hansen.'''
suppress_default_document_metadata_task = True

def task_document_metadata():
    task = dict()
    task['targets'] = [metadata_filenames['documents']]
    task['actions'] = [(generate_attributes_file,
                [dataset_dir+'/'+chron_list_filename, metadata_filenames['documents']])]
    task['clean'] = ['rm -f '+metadata_filenames['documents']]
    return task

def task_extract_data():
    task = dict()
    task['targets'] = [files_dir]
    task['actions'] = [
        (extract_state_of_the_union,
         [dataset_dir+'/'+chron_list_filename,
          dataset_dir+'/'+addresses_filename,
          files_dir]
        )
    ]
    task['clean'] = ['rm -rf '+files_dir]
    task['uptodate'] = [os.path.exists(files_dir)]
    return task
