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

from sys import argv
from string import punctuation, digits
from build.common.cleaner import Cleaner
import html2text
import re

class NYTCleaner(Cleaner):
    def __init__(self, input_dir, output_dir):
        super(NYTCleaner,self).__init__(input_dir, output_dir, u"-\n'", punctuation+digits)
        
    def cleaned_text(self, text):
        sans_html = html2text.html2text(text)
        
        sans_urls = sans_html
        urls = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', sans_html)
        for url in urls:
            sans_urls = sans_urls.replace(url, '')
        return super(NYTCleaner,self).cleaned_text(sans_urls)
    
    def new_filename(self, old_filename):
        return old_filename.replace('.html', '.txt')

def clean_nyt(src_dir, dest_dir):
    c = NYTCleaner(src_dir, dest_dir)
    c.clean()

if __name__ == '__main__':
    clean_nyt(argv[1], argv[2])