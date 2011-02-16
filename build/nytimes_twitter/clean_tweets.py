# coding: utf-8

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

from string import punctuation, digits
from build.common.cleaner import Cleaner
from sys import argv
import re

class TweetCleaner(Cleaner):
    def __init__(self, input_dir, output_dir):
        super(TweetCleaner, self).__init__(input_dir, output_dir, u"’“”\r\n'-/.,", punctuation + digits.replace('#', ''))

    def cleaned_text(self, text):
        urls = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', text)
        for url in urls:
            text = text.replace(url, '')
        text = text.replace('&quot;', '')
        text = text.replace('&lt;', '')
        text = text.replace('&gt;', '')
        text = text.replace('&amp;', '')
        text = re.sub('\\brt\\b', '', text)
        return super(TweetCleaner, self).cleaned_text(text)


def clean_tweets(src_dir, dest_dir):
    c = TweetCleaner(src_dir, dest_dir)
    c.clean()

if __name__ == '__main__':
    clean_tweets(argv[1], argv[2])
