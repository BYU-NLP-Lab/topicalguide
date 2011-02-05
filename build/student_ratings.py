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

import cjson

from build.common.cleaner import Cleaner
from build.common.util import create_dirs_and_open

data_dir = '/aml/data/mjg82/student_ratings/comments'

def get_dataset_name(locals):
    return "ratings-bio100"


def get_dataset_description(locals):
    return "Student Ratings"


def get_copy_dataset(locals):
    return True


def get_mallet_token_regex(locals):
    return r"[a-zA-Z]+"


def get_attributes_file(locals):
    return "{0}/attributes.json".format(locals['dataset_dir'])


def get_files_dir(locals):
    return locals['dataset_dir'] + "/files"


def task_attributes_file():
    targets = [attributes_file]
    actions = [(gen_attr_file, [data_dir, attributes_file])]
    clean = ["rm -f " + attributes_file]
    return {'targets': targets, 'actions': actions, 'clean': clean}


def task_dir_timestamp():
    return {'actions': [(directory_timestamp, [files_dir])]}


def task_copy_and_transform_dataset():
    actions = [
        (clean_ratings, [data_dir, files_dir])
    ]
    clean = [
        'rm -rf '+files_dir
    ]
    result_deps = ['dir_timestamp']
    return {'actions': actions, 'clean': clean, 'result_dep':result_deps}


def clean_ratings(src_dir, dest_dir):
    c = SubsetRatingsCleaner(src_dir, dest_dir, '', '')
    c.clean()


def skipping_condition(path):
    if 'BIO_100' not in path:
        return True
    if '20095' not in path:
        return True
    return False


def gen_attr_file(src_dir, output_file):
    file_dicts = []
    for root, dirs, files in os.walk(src_dir):
        partial_root = root.replace(src_dir, '')[1:]
        if skipping_condition(root): continue
        for f in files:
            c = SubsetRatingsCleaner(src_dir, '', '', '')
            in_path = '/'.join([src_dir, partial_root, f])
            try:
                text = open(in_path).read().decode('utf-8')
            except UnicodeDecodeError:
                continue
            cleaned_text = c.cleaned_text(text)
            if not cleaned_text: continue
            file_dicts.append({})
            file_dicts[-1]['path'] = '/'.join([partial_root, f])
            semester, department, course, section = partial_root.split('/')
            file_dicts[-1]['attributes'] = {}
            file_dicts[-1]['attributes']['semester'] = semester
            file_dicts[-1]['attributes']['department'] = department
            file_dicts[-1]['attributes']['course'] = course
            file_dicts[-1]['attributes']['section'] = section
    w = open(output_file, 'w')
    w.write(cjson.encode(file_dicts))
    w.close()


class SubsetRatingsCleaner(Cleaner):
    def clean(self):
        for root, dirs, files in os.walk(self.input_dir):
            if skipping_condition(root): continue
            # To create a similar structure in output_dir, we need to isolate
            # the part of root that is above input_dir
            # the [1:] takes off a leading /
            partial_root = root.replace(self.input_dir, '')[1:]
            for f in files:
                in_path = '/'.join([self.input_dir, partial_root, f])
                out_path = '/'.join([self.output_dir, partial_root, f])

                try:
                    text = open(in_path).read().decode('utf-8')
                except UnicodeDecodeError:
                    continue
                cleaned_text = self.cleaned_text(text)
                if cleaned_text:
                    f = create_dirs_and_open(out_path)
                    f.write(cleaned_text.encode('utf-8'))


