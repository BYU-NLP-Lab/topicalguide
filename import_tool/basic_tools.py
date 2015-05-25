from __future__ import division, print_function, unicode_literals
import os
import re
from DateTime import DateTime
from HTMLParser import HTMLParser
from visualize.models import MetadataType


def seperate_metadata_and_content(s):
    """
    Given a string the metadata is seperated from the content. The string must be in the following format:
    
    metadata_tag1: metadata_value1
    metadata_tag2: metadata_value2
    ...
    metadata_tagn: metadata_valuen
    <Two newlines>
    content
    content
    
    content
    ...
    
    Returns (metadata, content)
    
    If no metadata is present then an empty string is returned, same with content.
    """
    m_and_c = s.split('\n\n', 1)
    metadata = ''
    content = ''
    
    # normal case where we have metadata and content
    if len(m_and_c) == 2:
        metadata = m_and_c[0].strip()
        content = m_and_c[1].strip()
    # if we only have one of content or metadata this process determines which it is
    elif len(m_and_c) == 1:
        value = m_and_c[0].strip()
        if not len(value) == 0:
            lines = value.split('\n')
            is_metadata = True
            for l in lines:
                key_value = l.split(':', 1)
                if len(key_value) != 2:
                    is_metadata = False
                    break
            
            if is_metadata:
                metadata = value
            else:
                content = value
    
    return (metadata, content)

def metadata_to_dict(metadata):
    """
    Takes metadata as specified in seperate_metadata_and_content() documentation and\
    converts it to a dictionary.
    Note that white space on either side of the metadata tags and values will be stripped; \
    also, if there are any duplicate metadata key names, the value of the last duplicate will \
    be in the resulting dictionary.
    Also, the tags will have any spaces replaced with underscores and be set to lowercase.
    """
    result = {}
    lines = metadata.split('\n')
    for l in lines:
        key_value = l.split(':', 1)
        if len(key_value) == 2:
            key = key_value[0].strip().replace(' ', '_').lower()
            value = key_value[1].strip()
            result[key] = value
    return result

def get_all_files_from_directory(directory, recursive=False):
    """
    Set recursive to True to recursively find files.
    Return a list of absolute file paths starting at the given directory.
    """
    list_of_files = []
    
    for root, dirs, files in os.walk(directory, followlinks=recursive):
        for file in files:
            list_of_files.append(os.path.join(root, file))
    return list_of_files

def get_type(value):
    """
    Returns the type of value, value is a string.
    Returns one of the known types in the form of a string: 'int', 'float', 'bool', and 'text'.
    Example: If value = '34' then the type returned is 'int'.
    """
    try:
        int(value)
        return 'int'
    except:
        pass
    try:
        float(value)
        return 'float'
    except:
        pass
    lower_value = value.lower()
    if lower_value == 'true' or lower_value == 'false' or lower_value == 't' or lower_value == 'f':
        return 'bool'
    try:
        DateTime(value)
        return 'datetime'
    except:
        pass
    return 'text'

def verify_types(metadata_types, metadata, metadata_ordinal_sets={}):
    """Makes sure that the types in the metadata match the types in the
    given metadata_types. If there are extra keys or missing keys in metadata 
    they are ignored.
    metadata_ordinal_sets -- only used if metadata_types contains 'ordinal'; 
                             used to check for a valid value
    Return a list of the offending keys; empty list otherwise.
    """
    result = []
    for name, t in metadata_types.iteritems():
        if name in metadata:
            value = metadata[name]
            if t == MetadataType.ORDINAL:
                if value not in metadata_ordinal_sets[name]:
                    result.append(name)
            else:
                determined_type = MetadataType.determine_type(value)
                if t != determined_type:
                    if not MetadataType.is_supertype(t, determined_type):
                        result.append(name)
    return result

def collect_types(metadata_types, metadata, doc_meta_ordinal_sets={}):
    """
    Takes a dictionary metadata_types that keeps track of the types so far.
    For each key, value pair in metadata if the key is not present in \
    metadata_types then it is added and the type of the value is also added.
    Note that if there are conflicting types then the type in metadata_types is \
    degraded to 'text'.
    """
    for meta_key, meta_value in metadata.iteritems():
        t = MetadataType.determine_type(meta_value)
        if not meta_key in metadata_types:
            if meta_key in doc_meta_ordinal_sets:
                if meta_value in doc_meta_ordinal_sets[meta_key]:
                    t = MetadataType.ORDINAL
            metadata_types[meta_key] = t
        else:
            current_type = metadata_types[meta_key]
            if not current_type == t and current_type != MetadataType.TEXT:
                if meta_key in doc_meta_ordinal_sets and meta_value in doc_meta_ordinal_sets[meta_key]:
                    t = MetadataType.ORDINAL
                elif t == MetadataType.FLOAT and current_type == MetadataType.INTEGER:
                    t = MetadataType.FLOAT
                elif t == MetadataType.INTEGER and current_type == MetadataType.FLOAT:
                    t = current_type
                else:
                    t = MetadataType.TEXT
                metadata_types[meta_key] = t

def create_subdocuments(name, content, major_delimiter='\n', min_chars=1000):
    """
    Return a list of tuples where each tuple contains a subdocument name \
    and a subsequence of the original content.  Recombining each subdocument \
    content in the order the list is iterated over will yield the original content \
    (with varying white space.)  The arguments min and max specify the allowed sizes of \
    each subdocument by character count.  Note that the max may be exceeded on some occassions \
    if the remaining text doesn't consititute enough for another subdocument.  The \
    basic algorithm tries to split on new line boundaries since spliting on \
    white space alone may generate odd subdocuments.
    """
    subdoc_contents = {}
    subdoc_number = 0
    
    if content == '':
        subdoc_contents[subdoc_number] = ''
        subdoc_number += 1
    
    while content != '':
        #~ content = content.strip()
        index = 0
        while index < min_chars:
            index = content.find(major_delimiter, index + 1)
            if index < 0:
                subdoc_contents[subdoc_number] = content
                subdoc_number += 1
                content = ''
                break
            elif index >= min_chars:
                subdoc_contents[subdoc_number] = content[0: index]
                content = content[index:]
                if len(content) < min_chars:
                    subdoc_contents[subdoc_number] = subdoc_contents[subdoc_number] + content
                    content = ''
                subdoc_number += 1
    
    result = []
    for index in xrange(0, subdoc_number):
        result.append((name + '_subdoc' + str(index), subdoc_contents[index]))
    return result

def remove_html_tags(text, remove_entities=False):
    """Return string that has no HTML tags and removes HTML entities if specified."""
    class HTMLStripper(HTMLParser):
        def __init__(self):
            self.reset()
            self.content = []
        def handle_data(self, data):
            self.content.append(data)
        def handle_entityref(self, name):
            if not remove_entities:
                self.content.append('&' + name + ';')
        def handle_charref(self, name):
            if not remove_entities:
                self.content.append('&#' + name + ';')
        def get_content(self):
            return ''.join(self.content)
    stripper = HTMLStripper()
    stripper.feed(text)
    stripper.close()
    return stripper.get_content()

def replace_html_entities(text):
    """Return string with HTML entities replaced with unicode characters."""
    parser = HTMLParser()
    return parser.unescape(text)

def get_unicode_content(file_path, encoding=None):
    """
    Return a unicode string of the files contents using the given encoding.  If no encoding is given
    then chardet will be used to determine the encoding.
    Note that this uses the chardet library and may cause problems, if an error is thrown then
    a utf-8 encoding is assumed and unrecognize caracters are discarded.
    """
    from chardet.universaldetector import UniversalDetector
    
    try:
        if not encoding:
            detector = UniversalDetector()
            contents = ''
            with open(file_path, 'rb') as f:
                contents = f.read()
                detector.feed(contents)
            detector.close()
            determined_encoding = detector.result['encoding']
            return contents.decode(encoding=determined_encoding)
        else:
            with open(file_path, 'r') as f:
                return unicode(f.read(), encoding=encoding, errors='ignore')
    except UnicodeError:
        with open(file_path, 'r') as f:
            return unicode(f.read(), encoding='utf-8', errors='ignore')

def remove_punctuation(s):
    """Return a string without punctuation (only alpha, numeric, underscore and whitespace characters survive)."""
    result = ''
    for sub in re.finditer(r'[\w\s]+', s, re.UNICODE):
        result += sub.group(0)
    return result

# vim: et sw=4 sts=4
