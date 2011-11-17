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
from sys import argv
from string import punctuation, digits
from build.common.cleaner import Cleaner
from xml.dom.minidom import parseString
from nltk.tokenize import TreebankWordTokenizer

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

if __name__ == '__main__':
    clean_cr(argv[1], argv[2])