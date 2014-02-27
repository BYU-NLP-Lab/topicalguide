from __future__ import print_function

import os
import sys
import json
import imp
import re

from HTMLParser import HTMLParser

from xml.sax.saxutils import unescape

# This script unescapes xml escape sequences

gen_tools = imp.load_source('filename', '/local/cj264/topicalguide/import_tool/dataset_classes/generic_tools.py')
sep = gen_tools.GenericTools.seperate_metadata_and_content


def rewrite_files(directory):
    os.path.walk(directory, rewrite_file_func, None)

def rewrite_file_func(arg, dirname, names):
    for name in names:
        f = os.path.join(dirname, name)
        rewrite_file(f, f)

def rewrite_file(file_name, new_file):
    meta = ''
    content = ''
    print(file_name, new_file)
    with open(file_name, 'r') as f:
        meta, content = sep(f.read())
   
    entities = {'&#151;': '--', '&ldquo;': '"', '&rdquo;': '"', '&ndash;': '-', 
        '&rsquo;': '\'', '&amp;': '&', '&hellip': '...', '&nbsp;': ' ', 
        '&lsquo;': '\''}


    temp = 'temp.txt'
    with open(new_file, 'w') as f:
        f.write(meta)
        f.write('\n\n')
        f.write(unescape(content, entities))

def find_html_escape_sequences(arg, dirname, names):
    for name in names:
        meta = ''
        content = ''
        with open(os.path.join(dirname, name), 'r') as f:
            meta, content = sep(f.read())
            entities = re.findall(r'&[^;]*;', content)
            for e in entities:
                if len(e) < 10:
                    if e not in arg:
                        arg[e] = 1
                    else:
                        arg[e] = arg[e] + 1

def print_html_escape_sequences(directory):
    # Finds all escape sequences used and a count of how often they are used
    arg = {}
    os.path.walk(directory, find_html_escape_sequences, arg)
    for k in arg:
        print(k + " " + str(arg[k]))

if __name__ == "__main__":
    print("Starting conversion.")
    # First find the escape sequences, then find and replace them once entities is updated
    print_html_escape_sequences('documents')
    #~ rewrite_files('documents')
