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
import os
from build.kcna.extract_docs import extract

dataset_name = "kcna"
dataset_description = "News releases/propaganda from North Korea's Korean Central News Agency (KCNA)"
url = "http://kcna.co.jp/"
data_dir = os.environ['HOME'] + "/Data"
kcna_dir = data_dir + "/kcna.co.jp"

def task_download_kcna():
    actions = ["mkdir -p {kcna_dir} && cd {kcna_dir}  && wget --mirror -nH {url}".format(kcna_dir=kcna_dir,url=url)]
    clean = ["rm -rf " + kcna_dir]
    return {'actions':actions, 'clean':clean, 'uptodate':[os.path.exists(kcna_dir)]}

def task_copy_and_transform_dataset():
    targets = [attributes_file]
    actions = ["mkdir -p "+files_dir,
               (extract, [kcna_dir, files_dir, attributes_file])]
    clean = ['rm -rf '+files_dir]
    task_deps = ['download_kcna']
    return {'targets': targets, 'actions': actions, 'clean': clean, 'task_dep': task_deps, 'uptodate': [os.path.exists(files_dir)]}

#def task_mallet_imported_data():
#    task = dict()
#    task['targets'] = [mallet_imported_data]
#    cmd = '{0} import-dir --input {1} --output {2} --keep-sequence --set-source-by-name --remove-stopwords'.format(mallet, files_dir, mallet_imported_data)
#    if token_regex is not None:
#        cmd += " --token-regex "+token_regex
#    task['actions'] = [cmd]
#    task['clean'] = ["rm -f "+mallet_imported_data]
#    task['task_dep'] = ['copy_and_transform_dataset']
#    return task
