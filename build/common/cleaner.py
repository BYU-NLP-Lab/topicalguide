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

class Cleaner(object):
    def __init__(self, input_dir, output_dir, replace_with_space, delete, show_text=False):
        self.replace_with_space = replace_with_space
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.delete_me = delete
        self.show_text = show_text
        
    def cleaned_text(self, text):
        lowered = text.lower()
        stripped = lowered.strip()
        replaced = self.replace(stripped)
        deleted = self.delete(replaced)
        reconstructed = self.reconstruct(deleted)
        return reconstructed
    
    def delete(self, text):
        for s in self.delete_me:
            text = text.replace(s, '')
        return text
    
    def replace(self, text):
        for s in self.replace_with_space:
            text = text.replace(s, ' ')
        return text
    
    def reconstruct(self, text):
        return self.reconstruct_arr(text.split(None))
    
    def reconstruct_arr(self, arr):
        new_text = u''
        for i in range(0,len(arr)):
            new_text += arr[i]
            if i < len(arr)-1: new_text += u' '
        return new_text
    
    def clean(self):
        for filename in os.listdir(self.input_dir):
            print filename
            in_path = '{0}/{1}'.format(self.input_dir, filename)
            out_path = '{0}/{1}'.format(self.output_dir, self.new_filename(filename))
            
            text = codecs.open(in_path, 'r', 'utf-8').read()
            cleaned_txt = self.cleaned_text(text)
            
            print '.',
            if self.show_text:
                print '\t' + text
                print '\t' + cleaned_txt
            
            codecs.open(out_path, 'w', 'utf-8').write(cleaned_txt)
    
    def new_filename(self, old_filename):
        return old_filename