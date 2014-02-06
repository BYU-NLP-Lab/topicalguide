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

#Congressional Bills Dataset build settings
import os

def directory_timestamp(dir_):
    return str(os.path.getmtime(dir_))

def update_config(c):
    c['data_dir'] = os.environ['HOME'] + "/Data"
    c['govtrack_dir'] = c['data_dir'] + "/govtrack.us"
    c['rsync_dest_dir'] = c['govtrack_dir'] + "/111"
    c['bills_dir'] = c['rsync_dest_dir'] + "/bills"
    c['dataset_name'] = "bills"
    c['dataset_description'] = "Text of legislation from the 111th United States Congress"
    c['token_regex'] = r"[a-zA-Z]+"

def create_tasks(c):

    def task_hash_cr():
        return {'actions': [(directory_timestamp, [c['bills_dir']])],
                'task_dep':['download_congressional_record']}

    #def task_attributes_file():
    #    targets = [attributes_file]
    #    actions = [(generate_attributes_file, [mallet_input, attributes_file])]
    #    file_deps = [mallet_input]
    #    clean = ["rm -f "+attributes_file]
    #    return {'targets':targets, 'actions':actions, 'file_dep':file_deps, 'clean':clean}

    def task_download_congressional_record():
        actions = ["rsync -az --delete --delete-excluded govtrack.us::govtrackdata/us/bills.txt/111 "+c['rsync_dest_dir']]
        clean = ["rm -rf " + c['bills_dir']]
        return {'actions':actions, 'clean':clean}

    def task_extract_data():
        actions = [
            (clean_bills, [c['bills_dir'],c['files_dir']])
        ]
        clean = [
            'rm -rf '+c['files_dir']
        ]
        
        result_deps = ['hash_cr']
        return {'actions': actions, 'clean': clean, 'result_dep':result_deps}

    return [task_hash_cr, task_download_congressional_record, task_extract_data]

