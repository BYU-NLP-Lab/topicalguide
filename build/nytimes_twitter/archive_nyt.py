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

from time import sleep, time
import re
import urllib
import feedparser
import html2text
import hashlib
import os
from string import punctuation, digits, maketrans, translate

class NYTArchiver(object):
    def __init__(self, output_dir):
        super(NYTArchiver,self).__init__()
        self.output_dir = output_dir
        self.cleanup_table = maketrans("-\n'","   ")
        self.empty_table = maketrans('','')
        self.delete_me = punctuation + digits
        
    def run(self, duration_in_seconds):
        nyt_path = self.output_dir + '/nytimes.com/'
        if not os.path.exists(nyt_path): os.mkdir(nyt_path)
        start_time = time()
        pattern = re.compile(r'<div class="articleBody">(.+?)</div>', re.DOTALL)
        
        while time() - start_time < duration_in_seconds:
            feed = feedparser.parse("http://feeds.nytimes.com/nyt/rss/Politics")
            for item in feed['items']:
                if "www.nytimes.com" in item.id:
                    path = nyt_path + item.id.replace('http://www.nytimes.com/', 'nytimes_').replace('/','_')
                    if not os.path.exists(path):
                        print item.id + ' -> ' + path
                        page = urllib.urlopen(item.id).read()
                        
                        text = ''
                        for m in pattern.finditer(page):
                            text += m.group(1).strip()
                        cleaned_text = self.cleaned(text)
                        
                        f = open(path, 'w')
                        f.write(cleaned_text)
            sleep(300)
    
    def cleaned(self,text):
        return text

if __name__ == '__main__':
    duration = 7*24*60*60
    output_dir = os.environ['HOME'] + '/Data'
    a = NYTArchiver(output_dir)
    a.run(duration)