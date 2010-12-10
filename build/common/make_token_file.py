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
import codecs
from sys import argv

def make_token_file(docs_dir, output_file):
    w = codecs.open(output_file, 'w', 'utf-8')
    
    for doc_filename in os.listdir(docs_dir):
        path = '{0}/{1}'.format(docs_dir, doc_filename)
        text = codecs.open(path, 'r', 'utf-8').read().strip().replace('\n',' ')
        w.write(u'{0} all {1}'.format(doc_filename, text))
        w.write(u'\n')

if __name__ == '__main__':
    make_token_file(argv[1], argv[2])