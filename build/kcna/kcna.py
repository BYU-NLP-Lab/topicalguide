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
import os
from build.kcna.extract_docs import extract

dataset_name = "kcna"
dataset_description = "News releases/propaganda from North Korea's Korean Central News Agency (KCNA)"
url = "http://kcna.co.jp/"
data_dir = os.environ['HOME'] + "/Data"
kcna_dir = data_dir + "/kcna.co.jp"
suppress_default_attributes_task = True

def task_download_kcna():
    task = dict()
    task['actions'] = ["mkdir -p {kcna_dir} && cd {kcna_dir}  && wget --mirror -nH {url}".format(kcna_dir=kcna_dir,url=url)]
    task['clean'] = ["rm -rf " + kcna_dir]
    task['uptodate'] = [os.path.exists(kcna_dir)]
    return task

def task_extract_data():
    task = dict()
    task['targets'] = [files_dir, attributes_file]
    task['actions'] = ["mkdir -p "+files_dir,
               (extract, [kcna_dir, files_dir, attributes_file])]
    task['clean'] = ['rm -rf '+files_dir, 'rm -f '+attributes_file]
    task['task_dep'] = ['download_kcna']
    task['uptodate'] = [os.path.exists(files_dir) and os.path.exists(attributes_file)]
    return task
