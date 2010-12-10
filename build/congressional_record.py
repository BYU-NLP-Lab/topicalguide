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

#Congressional Record Dataset build settings
import os
from build.cr.clean_cr import clean_cr
from build.cr.generate_attributes_file import generate_attributes_file

data_dir = os.environ['HOME'] + "/Data"
govtrack_dir = data_dir + "/govtrack.us"
rsync_dest_dir = govtrack_dir + "/111"
cr_dir = rsync_dest_dir + "/cr"

def get_dataset_name(locals):
    return "congressional_record"

def get_dataset_description(locals):
    return "Floor debate from the Congressional Record of the 111th United States Congress"

def get_copy_dataset(locals):
    return True

def get_mallet_token_regex(locals):
    return r"\\S+"

def get_attributes_file(locals):
    return "{0}/attributes.json".format(locals['dataset_dir'])

def get_files_dir(locals):
    return locals['dataset_dir'] + "/files"

def task_hash_cr():
    return {'actions': [(directory_recursive_hash, [cr_dir])],
            'task_dep':['download_congressional_record']}

def task_attributes_file():
    targets = [attributes_file]
    actions = [(generate_attributes_file, [mallet_input, attributes_file])]
    file_deps = [mallet_input]
    clean = ["rm -f "+attributes_file]
    return {'targets':targets, 'actions':actions, 'file_dep':file_deps, 'clean':clean}

def task_download_congressional_record():
    actions = ["rsync -az --delete --delete-excluded govtrack.us::govtrackdata/us/111/cr "+rsync_dest_dir]
    clean = ["rm -rf " + cr_dir]
    return {'actions':actions, 'clean':clean}

def task_copy_and_transform_dataset():
    actions = [
        "mkdir -p " + files_dir,
        (clean_cr, [cr_dir,files_dir])
    ]
    clean = [
        'rm -rf '+files_dir
    ]
    
    result_deps = ['hash_cr']
    return {'actions': actions, 'clean': clean, 'result_dep':result_deps}