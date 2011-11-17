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

#NYTimes/Twitter Dataset build settings
from build.nytimes_twitter.clean_nyt import clean_nyt
from build.nytimes_twitter.clean_tweets import clean_tweets
from build.nytimes_twitter.generate_attributes_file import generate_attributes_file

data_dir = os.environ['HOME'] + "/Data"
twitter_dir = data_dir + "/twitter.com"
nytimes_dir = data_dir + "/nytimes.com"
show_text = False

def get_dataset_name(locals):
    return "nytimes_twitter-politics"

def get_dataset_description(locals):
    return "A combination of New York Times political articles and Twitter political tweets"

def get_copy_dataset(locals):
    return True

def get_generate_attributes_file(locals):
    return True

def get_mallet_token_regex(locals):
    return r"\\S+"

def get_attributes_file(locals):
    return "{0}/attributes.json".format(locals['dataset_dir'])

def get_files_dir(locals):
    return locals['dataset_dir'] + "/files"

def task_hash_twitter():
    return {'actions': [(directory_timestamp, [twitter_dir])]}

def task_hash_nytimes():
    return {'actions': [(directory_timestamp, [nytimes_dir])]}

def task_attributes_file():
    targets = [attributes_file]
    actions = [(generate_attributes_file, [mallet_input, attributes_file])]
    file_deps = [mallet_input]
    clean = ["rm -f "+attributes_file]
    return {'targets':targets, 'actions':actions, 'file_dep':file_deps, 'clean':clean}

def task_copy_and_transform_dataset():
    actions = [
        "mkdir -p " + files_dir,
        (clean_tweets, [twitter_dir,files_dir]),
        (clean_nyt,    [nytimes_dir,files_dir])
    ]
    clean = [
        'rm -rf '+files_dir
    ]
    
    result_deps = ['hash_twitter', 'hash_nytimes']
    return {'actions': actions, 'clean': clean, 'result_dep':result_deps}