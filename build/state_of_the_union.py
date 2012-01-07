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

from backend import c

def initialize_config(config):
    config['num_topics'] = 100
    config['chron_list_filename'] = 'chronological_list.wiki'
    config['addresses_filename'] = 'state_of_the_union_addresses.txt'
    config['dataset_name'] = 'state_of_the_union'
    config['dataset_readable_name'] = 'State of the Union Addresses 1790-2010'
    config['dataset_description'] = \
    '''State of the Union Addresses taken from WikiSource by adding all
     addresses to a "book" and downloading it. Created by Josh Hansen.'''
    config['suppress_default_document_metadata_task'] = True
    config['metadata_filenames'] = lambda c: {
          'datasets': '%s/datasets.json' % c['raw_data_dir']
    }

def task_document_metadata():
    doc_meta_filename = c['metadata_filenames']['documents']
    task = dict()
    task['targets'] = [doc_meta_filename]
    task['actions'] = [(generate_attributes_file,
                ['%s/%s' % (c['raw_data_dir'], c['chron_list_filename']), doc_meta_filename])]
    task['clean'] = ['rm -f '+doc_meta_filename]
    return task

def task_extract_data():
    def utd(_task, _vals): return os.path.exists(c['files_dir'])
        
    task = dict()
    task['targets'] = [c['files_dir']]
    task['actions'] = [
        (extract_state_of_the_union,
         ['%s/%s' % (c['raw_data_dir'], c['chron_list_filename']),
          '%s/%s' % (c['raw_data_dir'], c['addresses_filename']),
          c['files_dir']]
        )
    ]
    task['clean'] = ['rm -rf '+c['files_dir']]
    task['uptodate'] = [utd]
    return task




chron_entry_regex = r"\[\[(?P<title>(?P<president_name>.+)'s? .*State of the Union (?:Address|Speech))\|(?P<address_number>\w+) State of the Union Address\]\] - \[\[author:(?P<author_name>.+)\|.+\]\], \((?P<day>\d+) (?P<month>\w+) \[\[w:(?P<year>\d+)\|(?P=year)\]\]\)"
def metadata(chron_list_wiki_file):
    text = codecs.open(chron_list_wiki_file,'r','utf-8').read()
    return [m for m in re.finditer(chron_entry_regex, text, re.IGNORECASE)]

ordinal_to_cardinal = {'First':1,'Second':2,'Third':3,'Fourth':4,'Fifth':5,'Sixth':6,'Seventh':7,'Eighth':8,'Ninth':9,'Tenth':10,'Eleventh':11,'Twelfth':12}
def filename(metadata):
    return metadata.group('president_name').replace(' ','_') + "_" + str(ordinal_to_cardinal[metadata.group('address_number')]) + '.txt'

def extract_state_of_the_union(chron_list_filename, addresses_filename, dest_dir):
    tokenizer = TreebankWordTokenizer()
    def lines_to_string(lines):
        raw_txt = u' '.join(lines)
        tokens = tokenizer.tokenize(raw_txt)
        tokenized_txt = u' '.join(tokens)
        return tokenized_txt
    
    print "extract_state_of_the_union({0},{1},{2})".format(chron_list_filename, addresses_filename, dest_dir)
#    titles = [m.group('title') for m in meta]
    titles = dict()
    for m in metadata(chron_list_filename):
        titles[m.group('title')] = m
    
    print 'Addresses in index: ' + str(len(titles))
    extracted_count = 0
    if not os.path.exists(dest_dir): os.mkdir(dest_dir)
    
    
    current_speech_title = None
    lines = []
    for line in codecs.open(addresses_filename,'r','utf-8'):
        line = line.strip()
        if line in titles:
            if current_speech_title is not None:
                m = titles[current_speech_title]
                w = codecs.open(dest_dir+'/'+filename(m),'w','utf-8')
                w.write(lines_to_string(lines))
                lines = []
                print 'Extracted "{0}"'.format(current_speech_title)
                extracted_count += 1
            current_speech_title = line
        else:
            lines += [line]
    
    m = titles[current_speech_title]
    w = codecs.open(dest_dir+'/'+filename(m),'w','utf-8')
    w.write(lines_to_string(lines))
    print 'Extracted "{0}"'.format(current_speech_title)
    extracted_count += 1
    print 'Addresses extracted: ' + str(extracted_count)
    print 'Missed: ' + str(len(titles)-extracted_count)




head = '''{
    "types": {
        "address_number": "int",
        "title": "text",
        "author_name": "text",
        "month": "text",
        "president_name": "text",
        "year": "int",
        "day": "int"
    },
    "data": {'''

tail = '''\t}
}'''

address_nums = {'First':1, 'Second':2, 'Third':3, 'Fourth':4, 'Fifth':5,
    'Sixth':6, 'Seventh':7, 'Eighth':8, 'Ninth':9, 'Tenth':10, 'Eleventh':11,
    'Twelfth':12}

def generate_attributes_file(chron_list_file, output_file):
    print "Building attributes file {0} using {1}".format(output_file, chron_list_file)
    
    meta = metadata(chron_list_file)
    w = open(output_file, 'w')
    
    w.write(head)
    w.write('\n')
    for i,m in enumerate(meta):
        w.write('\t\t"%s": {\n' % filename(m))
        
        attr_entries = []
        for attr,val in m.groupdict().items():
            if attr=="address_number": val=address_nums[val]
            attr_entries += ['\t\t\t"{0}": "{1}"'.format(attr,val)]
        w.write(',\n'.join(attr_entries))
        w.write('\n\t\t}')
        
        if i < len(meta)-1: w.write(',')
        
        w.write('\n')
    w.write(tail)