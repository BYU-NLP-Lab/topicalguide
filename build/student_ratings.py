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

import topic_modeling.anyjson as anyjson

from build import Cleaner
from build import create_dirs_and_open

data_dir = '/aml/data/mjg82/student_ratings/comments'

dataset_name = "ratings-music101"
dataset_description = "Student Ratings"

mallet_num_iterations = 300

def create_tasks(c):

    def task_attributes():
        task = dict()
        task['targets'] = [attributes_file]
        task['actions'] = [(gen_attr_file, [data_dir, attributes_file])]
        task['clean'] = ["rm -f " + attributes_file]
        task['uptodate'] = [os.path.exists(attributes_file)]
        return task

    def task_extract_data():
        task = dict()
        task['targets'] = [files_dir]
        task['actions'] = [(clean_ratings, [data_dir, files_dir])]
        task['clean'] = ['rm -rf '+files_dir]
        task['uptodate'] = [os.path.exists(files_dir)]
        return task

    return [task_attributes, task_extract_data]

def clean_ratings(src_dir, dest_dir):
    c = SubsetRatingsCleaner(src_dir, dest_dir, '', '')
    c.clean()

def skipping_condition(path):
    if 'MUSIC_101/002' not in path:
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
    w.write(anyjson.serialize(file_dicts))
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



