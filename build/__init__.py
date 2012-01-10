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

class Cleaner(object):
    def __init__(self, input_dir, output_dir, replace_with_space, delete,
            show_text=False):
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
        # root is the full path of the directory, dirs is the list of
        # directories in root, and files is the list of files in root
        for root, _dirs, files in os.walk(self.input_dir):
            # To create a similar structure in output_dir, we need to isolate
            # the part of root that is above input_dir
            # the [1:] takes off a leading /
            partial_root = root.replace(self.input_dir, '')[1:]
            for f in files:
                in_path = '/'.join([self.input_dir, partial_root, f])
                out_path = '/'.join([self.output_dir, partial_root, f])

                text = open(in_path).read().decode('utf-8')
                cleaned_text = self.cleaned_text(text)
                if cleaned_text:
                    f = create_dirs_and_open(out_path)
                    f.write(cleaned_text.encode('utf-8'))

    def new_filename(self, old_filename):
        return old_filename

def create_dirs_and_open(filename):
    """This assumes that you want to open the file for writing.  It doesn't
    make much sense to create directories if you are not going to open for
    writing."""
    try:
        return codecs.open(filename, 'w', 'utf-8')
    except IOError as e:
        import errno
        if e.errno != errno.ENOENT:
            raise
    directory = filename.rsplit('/', 1)[0]
    _try_makedirs(directory)
    return open(filename, 'w')

def _try_makedirs(path):
    """Do the equivalent of mkdir -p."""
    try:
        os.makedirs(path)
    except OSError, e:
        import errno
        if e.errno != errno.EEXIST:
            raise