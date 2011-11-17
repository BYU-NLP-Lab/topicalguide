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
import codecs
from sys import argv

def make_token_file(docs_dir, output_file):
    w = codecs.open(output_file, 'w', 'utf-8')
    
    for root, dirs, files in os.walk(docs_dir):
        for f in files:
            path = '{0}/{1}'.format(root, f)
            # the [1:] takes off a leading /
            partial_root = root.replace(docs_dir, '')[1:]
            if partial_root:
                mallet_path = '{0}/{1}'.format(partial_root, f)
            else:
                mallet_path = f
            text = open(path).read().decode('utf-8').strip().replace('\n',' ').replace('\r',' ')
            w.write(u'{0} all {1}'.format(mallet_path, text))
            w.write(u'\n')

if __name__ == '__main__':
    make_token_file(argv[1], argv[2])
