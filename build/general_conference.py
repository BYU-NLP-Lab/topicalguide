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

data_dir = '/aml/data/mjg82/gc++'

dataset_name = "gc++"
dataset_description = """General Conference Talks from 1900-2011

Plus a few extras...  This has a number of BYU devotionals and CES firesides,
though it is by no means exhaustive there.  And the data is a little noisy."""

num_topics = 250
mallet_num_iterations = 10000

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
    task['actions'] = [(clean_gc, [data_dir, files_dir])]
    task['clean'] = ['rm -rf '+files_dir]
    task['uptodate'] = [os.path.exists(files_dir)]
    return task


def clean_gc(src_dir, dest_dir):
    c = GCCleaner(src_dir, dest_dir, '', '')
    c.clean()


def skipping_condition(path):
    return False


def gen_attr_file(src_dir, output_file):
    file_dicts = []
    for root, dirs, files in os.walk(src_dir):
        partial_root = root.replace(src_dir, '')[1:]
        if skipping_condition(root): continue
        for f in files:
            in_path = '/'.join([src_dir, partial_root, f])
            print in_path
            json = cjson.decode(open(in_path).read())
            file_dicts.append({})
            file_dicts[-1]['path'] = '/'.join([partial_root, f])
            file_dicts[-1]['attributes'] = {}
            file_dicts[-1]['attributes']['type'] = json['type']
            file_dicts[-1]['attributes']['gender'] = json['gender']
            file_dicts[-1]['attributes']['calling'] = json['calling']
            file_dicts[-1]['attributes']['gender'] = json['gender']
            file_dicts[-1]['attributes']['speaker'] = json['speaker']
            file_dicts[-1]['attributes']['year'] = str(json['year'])
            file_dicts[-1]['attributes']['month'] = str(json['month'])
            file_dicts[-1]['attributes']['day'] = str(json['day'])
    w = open(output_file, 'w')
    w.write(cjson.encode(file_dicts))
    w.close()


class GCCleaner(Cleaner):
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

                json = cjson.decode(open(in_path).read())
                cleaned_text = json['text']
                if cleaned_text:
                    f = create_dirs_and_open(out_path)
                    f.write(cleaned_text.encode('utf-8'))


