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
from string import punctuation, digits
from build import Cleaner
from xml.dom.minidom import parseString
from nltk.tokenize import TreebankWordTokenizer



def initialize_config(c):
    c['dataset_name'] = "congressional_record"
    c['dataset_description'] = "Floor debate from the Congressional Record of the 111th United States Congress"
    c['token_regex'] = r"\\w+"
    
    c['data_dir'] = os.environ['HOME'] + "/Data"
    c['govtrack_dir'] = c['data_dir'] + "/govtrack.us"
    c['rsync_dest_dir'] = c['govtrack_dir'] + "/111"
    c['cr_dir'] = c['rsync_dest_dir'] + "/cr"

from backend import c

#def task_attributes():
#    task = dict()
#    task['targets'] = [attributes_file]
#    task['actions'] = [(generate_attributes_file, [mallet_input, attributes_file])]
#    task['file_dep'] = [mallet_input]
#    task['clean'] = ["rm -f "+attributes_file]
#    return task

def task_download_congressional_record():
    task = dict()
    task['actions'] = ["rsync -az --delete --delete-excluded govtrack.us::govtrackdata/us/111/cr "+c['rsync_dest_dir']]
    task['clean'] = ["rm -rf " + c['cr_dir']]
    task['uptodate'] = [os.path.exists(c['rsync_dest_dir'])]
    return task

def task_extract_data():
    task = dict()
    task['targets'] = [c['files_dir']]
    task['actions'] = [(clean_cr, [c['cr_dir'],c['files_dir']])]
    task['clean'] = ['rm -rf '+c['files_dir']]
    task['task_dep'] = ['download_congressional_record']
    task['uptodate'] = [os.path.exists(c['files_dir'])]
    return task

#def generate_attributes_file(mallet_input_file, output_file):
#    print "Building attributes file {0} using {1}".format(output_file, mallet_input_file)
#    
#    f = open(mallet_input_file)
#    w = open(output_file, 'w')
#    
#    w.write('[\n')
#    lines = f.readlines()
#    for i in range(0,len(lines)):
#        arr = lines[i].split(None)
#        
#        w.write('\t{\n')
#        w.write('\t\t"attributes": {\n')
#        w.write('\t\t},\n')
#        w.write('\t\t"path": "' + arr[0] + '"\n')
#        
#        w.write('\t}')
#        
#        if i < len(lines)-1: w.write(',')
#        
#        w.write('\n')
#    w.write(']')

class CRCleaner(Cleaner):
    def __init__(self, input_dir, output_dir):
        super(CRCleaner,self).__init__(input_dir, output_dir, u"-\n'", punctuation+digits)
        self.t = TreebankWordTokenizer()
    
    def cleaned_text(self, text):
        if len(text) == 0:
            return u""
        sans_xml = self.xml_to_txt(text)
        arr = self.t.tokenize(sans_xml)
        return self.reconstruct_arr(arr)
    
    def xml_to_txt(self, xml):
        arr = []
        dom = parseString(xml)
        for node in (dom.firstChild.getElementsByTagName('speaking')+dom.firstChild.getElementsByTagName('speaking-unknown-id')):
            paragraphs = node.getElementsByTagName('paragraph')
            if len(paragraphs) > 0:
                for node2 in paragraphs:
                    if node2.hasChildNodes():
                        child = node2.firstChild
                        if child.nodeType == child.TEXT_NODE:
                            arr += [child.data.replace('&nbsp;',' ')]
        return ' '.join(arr)
    
    def new_filename(self, old_filename):
        return old_filename.replace('.xml', '.txt')

def clean_cr(src_dir, dest_dir):
    if not os.path.exists(dest_dir):
        os.mkdir(dest_dir)
        c = CRCleaner(src_dir, dest_dir)
        c.clean()
