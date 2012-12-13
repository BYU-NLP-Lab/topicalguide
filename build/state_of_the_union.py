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

#State of the Union Addresses Dataset build settings
import codecs
import os
import re
from nltk.tokenize import TreebankWordTokenizer

from build import create_dirs_and_open
from topic_modeling import anyjson

def update_config(c):
    c['num_topics'] = 100
    c['chron_list_filename'] = 'chronological_list.wiki'
    c['addresses_filename'] = 'state_of_the_union_addresses.txt'
    c['dataset_name'] = 'state_of_the_union'
    c['dataset_readable_name'] = 'State of the Union Addresses 1790-2010'
    c['suppress_default_document_metadata_task'] = True
    c['metadata_filenames'] = lambda c: {'datasets':
            '%s/datasets.json' % c['raw_data_dir']}
    c['pairwise_document_metrics'] = ['topic_correlation']

def create_tasks(c):
    NUMBER_OF_ADDRESSES = 223
    def task_extract_data():
        index_filename = '%s/%s' % (c['raw_data_dir'], c['chron_list_filename'])
        data_filename = '%s/%s' % (c['raw_data_dir'], c['addresses_filename'])
        dest_dir = c['files_dir']
        doc_meta_filename = c['metadata_filenames']['documents']

        def utd(_task, _vals):
            return len(os.listdir(dest_dir))==NUMBER_OF_ADDRESSES and os.path.exists(doc_meta_filename)

        task = dict()
        task['targets'] = [dest_dir, doc_meta_filename]
        task['actions'] = [(_extract, [index_filename, data_filename, dest_dir, doc_meta_filename])]
        task['clean'] = ['rm -rf '+dest_dir]
        task['uptodate'] = [utd]
        return task
    return [task_extract_data]

chron_entry_rgx_s = r"\[\[(?P<title>(?P<president_name>.+)'s? .*State of the Union (?:Address|Speech))\|(?P<address_number>\w+) State of the Union Address\]\] - \[\[author:(?P<author_name>.+)\|.+\]\], \((?P<day>\d+) (?P<month>\w+) \[\[w:(?P<year>\d+)\|(?P=year)\]\]\)"
chron_entry_rgx = re.compile(chron_entry_rgx_s, re.I)
nums = {'First':'1', 'Second':'2', 'Third':'3', 'Fourth':'4', 'Fifth':'5', 'Sixth':'6', 'Seventh':'7', 'Eighth':'8',
        'Ninth':'9', 'Tenth':'10', 'Eleventh':'11', 'Twelfth':'12'}
def _filename(chron_entry_d):
    prez = chron_entry_d['president_name'].replace(' ','_')
    num = chron_entry_d['address_number']
    return '%s_%s.txt' % (prez, num)

_tokenizer = TreebankWordTokenizer()
def _lines_to_string(lines):
    raw_txt = u' '.join(lines)
    tokens = _tokenizer.tokenize(raw_txt)
    tokenized_txt = u' '.join(tokens)
    return tokenized_txt

def _extract_metadata(chron_list_filename):
    metadata_text = codecs.open(chron_list_filename,'r','utf-8').read()
    metadata_data = {}
    titles_to_filenames = {}
    for m in chron_entry_rgx.finditer(metadata_text):
        d = m.groupdict()
        d['address_number'] = int(nums[d['address_number']])
        filename = _filename(d)
        titles_to_filenames[d['title']] = filename
        metadata_data[filename] = d
    if not len(metadata_data.keys()):
        raise Exception('No Addresses Found! (empty metadata listing)')
    return metadata_data, titles_to_filenames

def _write_metadata(metadata_data, dest_filename):
    metadata_types = {
        "address_number": "int",
        "title": "text",
        "author_name": "text",
        "month": "text",
        "president_name": "text",
        "year": "int",
        "day": "int"
    }
    metadata = {'types':metadata_types, 'data':metadata_data}
    w = create_dirs_and_open(dest_filename)
    w.write(anyjson.serialize(metadata))
    w.close()

def _extract_doc(doc_filename, title, lines):
    w = create_dirs_and_open(doc_filename)
    w.write(_lines_to_string(lines))
    w.close()
    print 'Extracted "{0}"'.format(title)

def _extract(chron_list_filename, addresses_filename, dest_dir, doc_metadata_filename):
    print "extract_state_of_the_union({0},{1},{2})".format(chron_list_filename,
            addresses_filename, dest_dir)
    metadata_data, titles_to_filenames = _extract_metadata(chron_list_filename)
    _write_metadata(metadata_data, doc_metadata_filename)

    print 'Addresses in index: ' + str(len(titles_to_filenames))
    count = 0
    title = None
    lines = []
    for line in codecs.open(addresses_filename, 'r', 'utf-8'):
        line = line.strip()
        if line in titles_to_filenames:
            if title is not None:
                filename = '%s/%s' % (dest_dir, titles_to_filenames[title])
                _extract_doc(filename, title, lines)
                lines = []
                count += 1
            title = line
        else:
            lines += [line]
    filename = '%s/%s' % (dest_dir, titles_to_filenames[title])
    _extract_doc(filename, title, lines)
    count += 1

    print 'Addresses extracted: ' + str(count)
    if count < len(titles_to_filenames):
        raise Exception('Some addresses were not extracted')

