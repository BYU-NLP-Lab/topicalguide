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

#Congressional Record Dataset build settings
import os
from build.govtrack.cr.clean_cr import clean_cr
from build.govtrack.cr.generate_attributes_file import generate_attributes_file

dataset_name = "congressional_record"
dataset_description = "Floor debate from the Congressional Record of the 111th United States Congress"
token_regex = r"\\w+"

data_dir = os.environ['HOME'] + "/Data"
govtrack_dir = data_dir + "/govtrack.us"
rsync_dest_dir = govtrack_dir + "/111"
cr_dir = rsync_dest_dir + "/cr"

def task_attributes():
    task = dict()
    task['targets'] = [attributes_file]
    task['actions'] = [(generate_attributes_file, [mallet_input, attributes_file])]
    task['file_dep'] = [mallet_input]
    task['clean'] = ["rm -f "+attributes_file]
    return task

def task_download_congressional_record():
    task = dict()
    task['actions'] = ["rsync -az --delete --delete-excluded govtrack.us::govtrackdata/us/111/cr "+rsync_dest_dir]
    task['clean'] = ["rm -rf " + cr_dir]
    task['uptodate'] = [os.path.exists(rsync_dest_dir)]
    return task

def task_extract_data():
    task = dict()
    task['targets'] = [files_dir]
    task['actions'] = [(clean_cr, [cr_dir,files_dir])]
    task['clean'] = ['rm -rf '+files_dir]
    task['task_dep'] = ['download_congressional_record']
    task['uptodate'] = [os.path.exists(files_dir)]
    return task
