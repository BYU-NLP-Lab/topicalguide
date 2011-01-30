# The Topic Browser
# Copyright 2010-2011 Brigham Young University
#
# This file is part of the Topic Browser <http://nlp.cs.byu.edu/topic_browser>.
#
# The Topic Browser is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published by the
# Free Software Foundation, either version 3 of the License, or (at your
# option) any later version.
#
# The Topic Browser is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Affero General Public License
# for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with the Topic Browser.  If not, see <http://www.gnu.org/licenses/>.
#
# If you have inquiries regarding any further use of the Topic Browser, please
# contact the Copyright Licensing Office, Brigham Young University, 3760 HBLL,
# Provo, UT 84602, (801) 422-9339 or 422-3821, e-mail copyright@byu.edu.

#State of the Union Addresses Dataset build settings
from build.state_of_the_union.extract_sotua_documents import extract_state_of_the_union
from build.state_of_the_union.generate_attributes_file import generate_attributes_file
import os

chron_list_filename = 'chronological_list.wiki'
addresses_filename = 'state_of_the_union_addresses.txt'
dataset_name = "state_of_the_union"
dataset_description = "State of the Union Addresses 1790-2010"

def task_attributes_file():
    targets = [attributes_file]
    actions = [(generate_attributes_file,
                [dataset_dir+'/'+chron_list_filename, attributes_file])]
    clean = ["rm -f "+attributes_file]
    return {'targets':targets, 'actions':actions, 'clean':clean}

#def task_dir_timestamp():
#    return {'actions': [(directory_timestamp, [files_dir])]}

def task_copy_and_transform_dataset():
    actions = [
        (extract_state_of_the_union,
         [dataset_dir+'/'+chron_list_filename,
          dataset_dir+'/'+addresses_filename,
          files_dir]
        )
    ]
    clean = [
        'rm -rf '+files_dir
    ]
#    result_deps = ['dir_timestamp']
    return {'actions': actions, 'clean': clean, 'uptodate': [os.path.exists(files_dir)]}