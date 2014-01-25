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
import json
from nltk.tokenize import TreebankWordTokenizer

from build import create_dirs_and_open
from topic_modeling import anyjson
from import_tool.Project import Project



def create_tasks(c):
    project = Project("/local/cj264/topicalguide/raw-data/conference_talks")
    print(c['raw_data_dir'])
    print c['metadata_filenames']['documents']
    
    def task_extract_data():
        dest_dir = c['files_dir']
        doc_meta_filename = c['metadata_filenames']['documents']
        
        def utd(_task, _vals):
            return len(os.listdir(dest_dir))==project.get_number_of_documents() and os.path.exists(doc_meta_filename)
        
        task = dict()
        task['targets'] = [dest_dir, doc_meta_filename]
        task['actions'] = [(_extract, [c, project])]
        task['clean'] = ['rm -rf '+dest_dir]
        task['uptodate'] = [utd]
        return task
    return [task_extract_data]


_tokenizer = TreebankWordTokenizer()
def _lines_to_string(lines):
    raw_txt = u' '.join(lines)
    tokens = _tokenizer.tokenize(raw_txt)
    tokenized_txt = u' '.join(tokens)
    return tokenized_txt

def _extract_doc(doc_filename, title, lines):
    w = create_dirs_and_open(doc_filename)
    w.write(_lines_to_string(lines))
    w.close()
    print 'Extracted "{0}"'.format(title)

def _extract(c, project):
    """\
    Extracts the documents and metadata from the directory
    given by the user to the Project object.
    """
    
    print("Extracting documents from project \"%s\""%project.get_project_name())
    
    #write all document metadata
    destination_file_name = c['metadata_filenames']['documents']
    w = create_dirs_and_open(destination_file_name)
    metadata = {'types':project.get_document_metadata_types(), \
                'data':project.get_all_documents_metadata()}
    w.write(json.dumps(metadata))
    w.close()
    
    #write documents
    doc_dest_dir = c['files_dir']
    project.copy_contents_to_directory(doc_dest_dir)


